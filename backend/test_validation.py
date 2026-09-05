from app.services.gemini_service import GeminiService


# Create the service without calling __init__
# This avoids needing Gemini API resources.
service = GeminiService.__new__(GeminiService)


def run_test(name, containers, summary, expected_status):
    result = service.validate_containers(
        {"containers": containers},
        summary
    )

    actual_status = result["validation"]["status"]

    print(f"\n{name}")
    print(f"Expected : {expected_status}")
    print(f"Actual   : {actual_status}")

    if actual_status == expected_status:
        print("RESULT   : PASS")
    else:
        print("RESULT   : FAIL")

    return actual_status == expected_status


# ==========================================================
# TEST 1
# Valid containers
# ==========================================================

test_1 = run_test(
    "TEST 1 - Valid Containers",

    [
        {
            "container_number": "HLBU1234567",
            "seal_number": "SEAL001",
            "size": "40 HC",
            "cartons": 1000,
            "weight_kg": 20000,
            "cbm": 50,
        },
        {
            "container_number": "MSCU7654321",
            "seal_number": "SEAL002",
            "size": "40 HC",
            "cartons": 2000,
            "weight_kg": 30000,
            "cbm": 70,
        },
    ],

    {
        "total_containers": 2,
        "total_cartons": 3000,
        "total_weight": 50000,
        "total_cbm": 120,
    },

    "PASS"
)


# ==========================================================
# TEST 2
# Duplicate container
# ==========================================================

test_2 = run_test(
    "TEST 2 - Duplicate Container",

    [
        {
            "container_number": "HLBU1234567",
            "seal_number": "SEAL001",
            "size": "40 HC",
            "cartons": 1000,
            "weight_kg": 20000,
            "cbm": 50,
        },
        {
            "container_number": "HLBU1234567",
            "seal_number": "SEAL002",
            "size": "40 HC",
            "cartons": 2000,
            "weight_kg": 30000,
            "cbm": 70,
        },
    ],

    {
        "total_containers": 2,
        "total_cartons": 3000,
        "total_weight": 50000,
        "total_cbm": 120,
    },

    "FAIL"
)


# ==========================================================
# TEST 3
# Missing container number
# ==========================================================

test_3 = run_test(
    "TEST 3 - Missing Container Number",

    [
        {
            "container_number": None,
            "seal_number": "SEAL001",
            "size": "40 HC",
            "cartons": 1000,
            "weight_kg": 20000,
            "cbm": 50,
        },
    ],

    {
        "total_containers": 1,
        "total_cartons": 1000,
        "total_weight": 20000,
        "total_cbm": 50,
    },

    "FAIL"
)


# ==========================================================
# TEST 4
# Missing optional CBM
# ==========================================================

test_4 = run_test(
    "TEST 4 - Missing Optional CBM",

    [
        {
            "container_number": "HLBU1234567",
            "seal_number": "SEAL001",
            "size": "40 HC",
            "cartons": 1000,
            "weight_kg": 20000,
            "cbm": None,
        },
    ],

    {
        "total_containers": 1,
        "total_cartons": 1000,
        "total_weight": 20000,
        "total_cbm": None,
    },

    "PASS"
)


# ==========================================================
# FINAL RESULT
# ==========================================================

all_tests = [
    test_1,
    test_2,
    test_3,
    test_4,
]

print("\n========================================")
print("FINAL VALIDATION TEST RESULT")
print("========================================")

if all(all_tests):
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")