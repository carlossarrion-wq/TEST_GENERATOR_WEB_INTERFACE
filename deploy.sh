#!/bin/bash
# deploy.sh - Automated deployment script

echo "🚀 Starting Test Plan Generator Lambda Deployment..."

FUNCTIONS=("test-plan-generator-plans-crud" "test-plan-generator-cases-crud" "test-plan-generator-chat-crud" "test-plan-generator-ai")

for FUNCTION in "${FUNCTIONS[@]}"; do
  echo "📦 Updating $FUNCTION..."
  
  # Determine correct Python file based on function name
  if [[ $FUNCTION == *"plans-crud"* ]]; then
    PYTHON_FILE="test_plans_crud.py"
  elif [[ $FUNCTION == *"cases-crud"* ]]; then
    PYTHON_FILE="test_cases_crud.py"
  elif [[ $FUNCTION == *"chat-crud"* ]]; then
    PYTHON_FILE="chat_messages_crud.py"
  elif [[ $FUNCTION == *"ai"* ]]; then
    PYTHON_FILE="ai_test_generator.py"
  fi
  
  # Create ZIP
  echo "Creating ZIP with ${PYTHON_FILE} and db_utils.py"
  zip ${FUNCTION}.zip ${PYTHON_FILE} db_utils.py
  
  # Update function
  aws lambda update-function-code \
    --function-name $FUNCTION \
    --zip-file fileb://${FUNCTION}.zip
  
  echo "✅ $FUNCTION updated successfully"
done

echo "🎉 All functions updated!"
