# ✅ Test Policy – AI Audit Document Analyzer

To ensure the integrity of each development phase, this project enforces strict test validation rules.  
These rules apply to all components and phases.

---

## 1. Test Execution

- All tests must be executed using:  
  `python -m pytest` (or equivalent fallback test runner)

- Output must be saved to:  
  `test_output.log`

---

## 2. Automatic Verification

- The `verify_tests.sh` script **must be run after every test execution**
- It checks for the following in `test_output.log`:

FAIL
FAILED
ERROR
Traceback
AssertionError
KeyError
ValueError
WARNING
test(s) failed
test(s) deselected
test(s) skipped

yaml
Copy
Edit

If any of these patterns are detected:
- The test is considered **failed**
- The task or phase **cannot** be marked complete
- Errors must be fixed and tests re-run

---

## 3. Completion Rules

No task or phase may be declared complete unless:
- ✅ All tests were executed  
- ✅ All tests passed  
- ✅ No warnings or soft fails occurred  
- ✅ Evidence of passing tests is documented in the `/test_results` folder  
- ✅ `verify_tests.sh` exits with code `0`

---

_Last updated: Phase 3 completion_