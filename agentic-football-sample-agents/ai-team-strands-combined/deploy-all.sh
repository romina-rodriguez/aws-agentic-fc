#!/bin/bash
set -e

# ============================================================================
# Deploy all 5 AI Team (Combined: Memory + Gateway) agents to Bedrock AgentCore
# ============================================================================
#
# Usage:
#   AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh          # deploy all
#   AWS_DEFAULT_REGION=us-east-1 ./deploy-all.sh ai-gk    # deploy one
#
# Automatically handles:
#   - Memory resource creation (if MEMORY_ID not set)
#   - Lambda IAM role + function deployment for tactical tools
#   - AgentCore MCP Gateway creation with NO AUTH
#   - Gateway target registration
#   - Agent deployment to AgentCore with both MEMORY_ID and GATEWAY_URL
#
# Override auto-setup by pre-setting GATEWAY_URL and/or MEMORY_ID.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/_build"

AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export AWS_DEFAULT_REGION

GATEWAY_NAME="afwc-tactical-tools"
LAMBDA_PREFIX="afwc-gateway-tool"
LAMBDA_ROLE_NAME="afwc-gateway-tool-lambda-role"
GW_ROLE_NAME="AfwcGatewayExecutionRole"

ALL_AGENTS=("ai-gk" "ai-def" "ai-mid" "ai-fwd1" "ai-fwd2")
TOOLS=("calculate_pass_options" "evaluate_shot" "find_open_space" "get_defensive_assignment")

if [ -n "$1" ]; then
  AGENTS=("$1")
else
  AGENTS=("${ALL_AGENTS[@]}")
fi

echo "=========================================="
echo "  AI Team (Combined) — Deploy Agents"
echo "  Memory + Gateway + Balanced Strategy"
echo "=========================================="
echo ""

# ------ Pre-flight ------
echo "Checking prerequisites..."

for cmd in agentcore aws python3; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "ERROR: '$cmd' not found."; exit 1
  fi
  echo "  $cmd: OK"
done

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
  echo "ERROR: No valid AWS credentials."; exit 1
}
export AWS_ACCOUNT_ID
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  AWS Region:  $AWS_DEFAULT_REGION"
echo ""

# ======================================================================
# MEMORY SETUP (skipped if MEMORY_ID is pre-set)
# ======================================================================

if [ -z "$MEMORY_ID" ]; then
  echo "=========================================="
  echo "  Step 0: Create Memory Resource"
  echo "=========================================="
  set +e
  CREATE_OUTPUT=$(python3 "$SCRIPT_DIR/create_memory.py" 2>&1)
  CREATE_EXIT=$?
  set -e
  echo "  $CREATE_OUTPUT"
  if [ $CREATE_EXIT -ne 0 ]; then
    echo "ERROR: create_memory.py failed."; exit 1
  fi
  MEMORY_ID=$(echo "$CREATE_OUTPUT" | sed -n 's/.*export MEMORY_ID=\([^ ]*\).*/\1/p')
  if [ -z "$MEMORY_ID" ]; then
    MEMORY_ID=$(echo "$CREATE_OUTPUT" | sed -n 's/.*Memory resource ready: \([^ ]*\).*/\1/p')
  fi
  if [ -z "$MEMORY_ID" ]; then
    echo "ERROR: Could not parse MEMORY_ID."; exit 1
  fi
  export MEMORY_ID
  echo "  ✅ MEMORY_ID: $MEMORY_ID"
  echo ""
else
  echo "Using pre-set MEMORY_ID: $MEMORY_ID"
  echo ""
fi

# ======================================================================
# GATEWAY SETUP (skipped if GATEWAY_URL is pre-set)
# ======================================================================

if [ -n "$GATEWAY_URL" ]; then
  echo "Using pre-set GATEWAY_URL: $GATEWAY_URL"
  echo ""
else
  # ---- Step 1: Lambda IAM Role ----
  echo "=========================================="
  echo "  Step 1: Lambda IAM Role"
  echo "=========================================="

  set +e
  LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" \
    --query 'Role.Arn' --output text 2>/dev/null)
  ROLE_EXISTS=$?
  set -e

  if [ $ROLE_EXISTS -ne 0 ]; then
    echo "  Creating Lambda execution role..."
    TRUST_POLICY='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    LAMBDA_ROLE_ARN=$(aws iam create-role \
      --role-name "$LAMBDA_ROLE_NAME" \
      --assume-role-policy-document "$TRUST_POLICY" \
      --query 'Role.Arn' --output text)
    aws iam attach-role-policy \
      --role-name "$LAMBDA_ROLE_NAME" \
      --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    echo "  Waiting 10s for role propagation..."
    sleep 10
  fi
  echo "  Role ARN: $LAMBDA_ROLE_ARN"
  echo ""

  # ---- Step 2: Deploy Lambda Functions ----
  echo "=========================================="
  echo "  Step 2: Deploy Lambda Functions"
  echo "=========================================="

  for tool in "${TOOLS[@]}"; do
    FUNC_NAME="${LAMBDA_PREFIX}-${tool//_/-}"
    TOOL_FILE="$SCRIPT_DIR/gateway_tools/${tool}.py"

    set +e
    aws lambda get-function --function-name "$FUNC_NAME" \
      --region "$AWS_DEFAULT_REGION" > /dev/null 2>&1
    FUNC_EXISTS=$?
    set -e

    TMPDIR=$(mktemp -d)
    cp "$TOOL_FILE" "$TMPDIR/lambda_function.py"
    sed -i'' -e 's/^def handler(/def lambda_handler(/' "$TMPDIR/lambda_function.py"
    (cd "$TMPDIR" && zip -q function.zip lambda_function.py)

    if [ $FUNC_EXISTS -ne 0 ]; then
      echo "  Creating: $FUNC_NAME"
      aws lambda create-function \
        --function-name "$FUNC_NAME" \
        --runtime python3.12 \
        --handler lambda_function.lambda_handler \
        --role "$LAMBDA_ROLE_ARN" \
        --zip-file "fileb://$TMPDIR/function.zip" \
        --timeout 10 --memory-size 128 \
        --region "$AWS_DEFAULT_REGION" > /dev/null
    else
      echo "  Updating: $FUNC_NAME"
      aws lambda update-function-code \
        --function-name "$FUNC_NAME" \
        --zip-file "fileb://$TMPDIR/function.zip" \
        --region "$AWS_DEFAULT_REGION" > /dev/null
    fi
    rm -rf "$TMPDIR"
  done
  echo ""

  # ---- Step 3: Gateway IAM Role ----
  echo "=========================================="
  echo "  Step 3: Gateway Execution Role"
  echo "=========================================="

  set +e
  GW_ROLE_ARN=$(aws iam get-role --role-name "$GW_ROLE_NAME" \
    --query 'Role.Arn' --output text 2>/dev/null)
  GW_ROLE_EXISTS=$?
  set -e

  if [ $GW_ROLE_EXISTS -ne 0 ]; then
    echo "  Creating gateway execution role..."
    GW_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"bedrock-agentcore.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    GW_ROLE_ARN=$(aws iam create-role \
      --role-name "$GW_ROLE_NAME" \
      --assume-role-policy-document "$GW_TRUST" \
      --query 'Role.Arn' --output text)
    aws iam put-role-policy \
      --role-name "$GW_ROLE_NAME" \
      --policy-name "InvokeLambdaTargets" \
      --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"lambda:InvokeFunction","Resource":"arn:aws:lambda:*:*:function:afwc-gateway-tool-*"}]}'
    echo "  Waiting 10s for role propagation..."
    sleep 10
  fi
  echo "  Role ARN: $GW_ROLE_ARN"
  echo ""

  # ---- Step 4: MCP Gateway + Targets ----
  echo "=========================================="
  echo "  Step 4: MCP Gateway + Register Targets"
  echo "=========================================="

  export GATEWAY_ROLE_ARN="$GW_ROLE_ARN"
  export LAMBDA_PREFIX
  export AWS_ACCOUNT_ID

  GW_OUTPUT=$(python3 "$SCRIPT_DIR/manage_gateway.py") || {
    echo "ERROR: manage_gateway.py failed."; exit 1
  }
  eval "$GW_OUTPUT"

  echo "  Gateway ID:  $GATEWAY_ID"
  echo "  Gateway URL: $GATEWAY_URL"
  echo ""
  export GATEWAY_URL
fi

# ======================================================================
# AGENT DEPLOYMENT
# ======================================================================

cleanup() {
  echo ""
  echo "Cleaning up build directory..."
  rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

DEPLOYED=()
FAILED=()

for agent in "${AGENTS[@]}"; do
  AGENT_SRC="$SCRIPT_DIR/$agent"
  STAGE="$BUILD_DIR/$agent"

  echo "=========================================="
  echo "  Deploying: $agent"
  echo "=========================================="

  if [ ! -d "$AGENT_SRC" ]; then
    echo "  ERROR: Agent directory not found: $AGENT_SRC"
    FAILED+=("$agent")
    continue
  fi

  rm -rf "$STAGE"
  mkdir -p "$STAGE/src"

  # Copy agent source
  cp "$AGENT_SRC/src/main.py" "$STAGE/src/main.py"

  # Copy shared lib
  if [ -d "$SCRIPT_DIR/../lib" ]; then
    LIB_SRC="$SCRIPT_DIR/../lib"
  elif [ -d "$SCRIPT_DIR/lib" ]; then
    LIB_SRC="$SCRIPT_DIR/lib"
  else
    echo "  ERROR: Shared lib not found."
    FAILED+=("$agent")
    continue
  fi
  mkdir -p "$STAGE/lib"
  cp "$LIB_SRC"/*.py "$STAGE/lib/"
  find "$STAGE/lib" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

  # Copy combined agent base files
  cp "$SCRIPT_DIR/combined_agent_base.py" "$STAGE/combined_agent_base.py"
  cp "$SCRIPT_DIR/combined_invoke_handler.py" "$STAGE/combined_invoke_handler.py"

  # Copy requirements
  cp "$AGENT_SRC/requirements.txt" "$STAGE/requirements.txt"

  # Generate .bedrock_agentcore.yaml from template
  sed \
    -e "s|\${AWS_ACCOUNT_ID}|$AWS_ACCOUNT_ID|g" \
    -e "s|\${AWS_DEFAULT_REGION}|$AWS_DEFAULT_REGION|g" \
    "$AGENT_SRC/.bedrock_agentcore.yaml.template" > "$STAGE/.bedrock_agentcore.yaml"

  echo "  Deploying from: $STAGE"
  REAL_PYTHON=$(python3 -c "import os,sys; print(os.path.realpath(sys.executable))")
  export UV_PYTHON="$REAL_PYTHON"
  export UV_PYTHON_PREFERENCE="only-system"
  if (cd "$STAGE" && agentcore deploy --auto-update-on-conflict \
    --env "GATEWAY_URL=$GATEWAY_URL" \
    --env "MEMORY_ID=$MEMORY_ID" \
    --env "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"); then
    echo "  ✅ $agent: DEPLOYED"
    DEPLOYED+=("$agent")
  else
    echo "  ❌ $agent: FAILED"
    FAILED+=("$agent")
  fi
  echo ""
done

# ======================================================================
# PERMISSIONS
# ======================================================================

echo "Attaching permissions to execution roles..."
set +e
EXEC_ROLES=$(aws iam list-roles \
  --query "Roles[?starts_with(RoleName, 'AmazonBedrockAgentCoreSDKRuntime-${AWS_DEFAULT_REGION}-')].RoleName" \
  --output text 2>/dev/null)
set -e

if [ -n "$EXEC_ROLES" ]; then
  for EXEC_ROLE_NAME in $EXEC_ROLES; do
    # Gateway permissions
    aws iam put-role-policy \
      --role-name "$EXEC_ROLE_NAME" \
      --policy-name AgentCoreGatewayAccess \
      --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
          \"Effect\": \"Allow\",
          \"Action\": [\"bedrock-agentcore:InvokeGateway\"],
          \"Resource\": \"arn:aws:bedrock-agentcore:${AWS_DEFAULT_REGION}:${AWS_ACCOUNT_ID}:gateway/*\"
        }]
      }" 2>/dev/null && echo "  ✅ Gateway permissions: $EXEC_ROLE_NAME" \
      || echo "  ⚠️  Failed gateway permissions: $EXEC_ROLE_NAME"

    # Memory permissions
    aws iam put-role-policy \
      --role-name "$EXEC_ROLE_NAME" \
      --policy-name AgentCoreMemoryAccess \
      --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [{
          \"Effect\": \"Allow\",
          \"Action\": [
            \"bedrock-agentcore:ListEvents\",
            \"bedrock-agentcore:CreateEvent\",
            \"bedrock-agentcore:GetEvent\",
            \"bedrock-agentcore:DeleteEvent\",
            \"bedrock-agentcore:RetrieveMemoryRecords\",
            \"bedrock-agentcore:GetMemoryRecord\",
            \"bedrock-agentcore:ListMemoryRecords\"
          ],
          \"Resource\": \"arn:aws:bedrock-agentcore:${AWS_DEFAULT_REGION}:${AWS_ACCOUNT_ID}:memory/*\"
        }]
      }" 2>/dev/null && echo "  ✅ Memory permissions: $EXEC_ROLE_NAME" \
      || echo "  ⚠️  Failed memory permissions: $EXEC_ROLE_NAME"
  done
else
  echo "  ⚠️  Could not find execution roles — attach policies manually"
fi
echo ""

# ------ Summary ------
echo "=========================================="
echo "  Deployment Summary"
echo "=========================================="
echo ""
echo "  Deployed: ${DEPLOYED[*]:-none}"
echo "  Failed:   ${FAILED[*]:-none}"
echo "  Account:  $AWS_ACCOUNT_ID"
echo "  Region:   $AWS_DEFAULT_REGION"
echo "  Gateway:  $GATEWAY_URL"
echo "  Memory:   $MEMORY_ID"
echo ""

if [ ${#FAILED[@]} -gt 0 ]; then
  echo "Some agents failed to deploy. Check output above."
  exit 1
fi

echo "All agents deployed successfully. 🏆"
