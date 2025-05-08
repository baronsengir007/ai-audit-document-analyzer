#!/bin/bash

echo "🧪 Running tests with pytest..."
pytest --tb=short > test_output.log 2>&1
PYTEST_EXIT=$?

echo -e "\n📄 Last 20 lines of test output:"
tail -n 20 test_output.log
echo -e "\n📦 Full test log saved to test_output.log"

# DEBUG: Print pytest exit code
echo "🔍 Pytest exit code: $PYTEST_EXIT"

# Check for failure indicators
if grep -Ei 'FAIL|ERROR|Traceback|AssertionError|KeyError|ValueError|FAILED' test_output.log > /dev/null; then
  echo "❌ Detected test failure patterns in test_output.log"
  exit 1
fi

if [ $PYTEST_EXIT -ne 0 ]; then
  echo "❌ Pytest returned non-zero exit code — tests failed"
  exit 1
fi

echo "✅ All tests passed successfully. No errors or warnings detected."
exit 0
