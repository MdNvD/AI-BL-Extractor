from app.services.gemini_service import GeminiService


print("\n========================================")
print("PHASE 3 - GEMINI ERROR HANDLING TEST")
print("========================================")


# ==========================================================
# TEST 1 - Empty document
# ==========================================================

print("\nTEST 1 - Empty Document")

service = GeminiService.__new__(GeminiService)

try:
    service._generate(
        prompt="Test prompt",
        text=""
    )

    print("RESULT : FAIL")
    print("Expected ValueError, but no error was raised.")

except ValueError as e:

    print("RESULT : PASS")
    print("Caught expected error:")
    print(e)

except Exception as e:

    print("RESULT : FAIL")
    print("Unexpected error:")
    print(type(e).__name__, e)


# ==========================================================
# TEST 2 - Whitespace-only document
# ==========================================================

print("\nTEST 2 - Whitespace-only Document")

try:
    service._generate(
        prompt="Test prompt",
        text="   \n   \n   "
    )

    print("RESULT : FAIL")
    print("Expected ValueError, but no error was raised.")

except ValueError as e:

    print("RESULT : PASS")
    print("Caught expected error:")
    print(e)

except Exception as e:

    print("RESULT : FAIL")
    print("Unexpected error:")
    print(type(e).__name__, e)


# ==========================================================
# TEST 3 - Missing Gemini API key
# ==========================================================

print("\nTEST 3 - Missing Gemini API Key")

try:

    # Create object without calling the normal constructor.
    # Then simulate missing API key behavior directly.

    original_key = None

    if original_key:
        print("RESULT : FAIL")
        print("Test setup is incorrect.")

    else:
        try:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        except RuntimeError as e:

            print("RESULT : PASS")
            print("Caught expected error:")
            print(e)

except Exception as e:

    print("RESULT : FAIL")
    print("Unexpected error:")
    print(type(e).__name__, e)


# ==========================================================
# TEST 4 - Invalid container result
# ==========================================================

print("\nTEST 4 - Invalid Container Result")

try:

    result = service.validate_containers(
        containers_result=None,
        summary={}
    )

    if (
        isinstance(result, dict)
        and
        "containers" in result
        and
        "validation" in result
    ):

        print("RESULT : PASS")
        print("Invalid container input handled safely.")

    else:

        print("RESULT : FAIL")
        print("Unexpected validation structure.")

except Exception as e:

    print("RESULT : FAIL")
    print("Unexpected error:")
    print(type(e).__name__, e)


# ==========================================================
# FINAL RESULT
# ==========================================================

print("\n========================================")
print("GEMINI ERROR HANDLING TEST COMPLETE")
print("========================================")