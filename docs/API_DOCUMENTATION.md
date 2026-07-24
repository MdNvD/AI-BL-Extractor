# 🌐 API Documentation

# AI Bill of Lading Extractor REST API

This document provides detailed information about the REST API endpoints used by the **AI Bill of Lading Extractor** application.

The backend is built using **FastAPI** and provides endpoints for uploading Bill of Lading PDFs, extracting shipment information using OCR and Google Gemini AI, and downloading the extracted results in Excel and JSON formats.

---

# 📌 Base URL

```
http://127.0.0.1:8000
```

---

# 📄 API Overview

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/upload` | Upload a Bill of Lading PDF |
| GET | `/api/bl-extract/{filename}` | Extract shipment information |
| GET | `/api/download/excel/{filename}` | Download Excel report |
| GET | `/api/download/json/{filename}` | Download JSON report |

---

# 1️⃣ Upload Bill of Lading PDF

## Endpoint

```
POST /api/upload
```

### Description

Uploads a Bill of Lading PDF file to the server.

Supported documents include:

- Digital PDFs
- Scanned PDFs
- Multi-page PDFs

---

### Request Type

```
multipart/form-data
```

---

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | PDF | ✅ Yes | Bill of Lading PDF file |

---

### Success Response

**Status Code:** `200 OK`

```json
{
  "filename": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.pdf"
}
```

---

### Error Responses

| Status | Description |
|--------|-------------|
| 400 | Invalid file format |
| 500 | Upload failed |

---

# 2️⃣ Extract Shipment Information

## Endpoint

```
GET /api/bl-extract/{filename}
```

### Description

Processes the uploaded Bill of Lading PDF.

The extraction workflow includes:

1. Read PDF
2. Detect digital or scanned document
3. Perform OCR when necessary
4. Send extracted text to Google Gemini AI
5. Return structured shipment information

---

### Path Parameter

| Parameter | Type | Description |
|-----------|------|-------------|
| filename | String | Uploaded PDF filename |

---

### Success Response

**Status Code:** `200 OK`

```json
{
  "header": {
    "carrier": "ABC Shipping",
    "bill_of_lading_number": "BL123456",
    "vessel": "MSC Example",
    "voyage": "V001",
    "port_of_loading": "Shanghai",
    "port_of_discharge": "Chennai",
    "place_of_receipt": "Shanghai",
    "place_of_delivery": "Chennai",
    "freight": "Prepaid",
    "shipper": "ABC Export Ltd",
    "consignee": "XYZ Imports",
    "notify_party": "XYZ Logistics"
  },

  "containers": [
    {
      "container_number": "MSCU1234567",
      "seal_number": "987654",
      "size": "40HC",
      "cartons": 1400,
      "weight": 29120,
      "cbm": 40
    }
  ],

  "summary": {
    "total_containers": 20,
    "total_cartons": 28000,
    "total_weight": 582400,
    "total_cbm": 800
  }
}
```

---

### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Uploaded file not found |
| 500 | AI extraction failed |

---

# 3️⃣ Download Excel Report

## Endpoint

```
GET /api/download/excel/{filename}
```

### Description

Downloads the extracted shipment information as an **Excel (.xlsx)** report.

The generated Excel file contains:

- Shipment Information
- Container Details
- Shipment Summary

---

### Success Response

**Status Code:** `200 OK`

Returns:

```
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

---

### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Excel file not found |
| 500 | Download failed |

---

# 4️⃣ Download JSON Report

## Endpoint

```
GET /api/download/json/{filename}
```

### Description

Downloads the extracted shipment information as a **JSON (.json)** file.

---

### Success Response

**Status Code:** `200 OK`

Returns:

```
application/json
```

---

### Error Responses

| Status | Description |
|--------|-------------|
| 404 | JSON file not found |
| 500 | Download failed |

---

# 🔄 API Workflow

```
                React Frontend
                      │
                      ▼
        Upload Bill of Lading PDF
                      │
                      ▼
             POST /api/upload
                      │
                      ▼
             Uploaded Filename
                      │
                      ▼
      GET /api/bl-extract/{filename}
                      │
                      ▼
          Detect PDF Type
         (Digital / Scanned)
               │        │
               ▼        ▼
          PyMuPDF   Tesseract OCR
               │        │
               └───┬────┘
                   ▼
          Extracted Document Text
                   ▼
           Google Gemini AI
                   ▼
       Structured Shipment Data
                   ▼
       Display Results in React UI
                   │
          ┌────────┴────────┐
          ▼                 ▼
 Download Excel      Download JSON
```

---

# 📊 HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Invalid request |
| 404 | Resource not found |
| 500 | Internal server error |

---

# 📦 Technologies Used

- FastAPI
- Python
- Google Gemini AI
- Tesseract OCR
- PyMuPDF
- Pandas
- OpenPyXL

---

# 📝 Notes

- Supports both digital and scanned Bill of Lading PDFs.
- Automatically switches to OCR when embedded text is unavailable.
- Uses Google Gemini AI for intelligent information extraction.
- Returns structured shipment information in JSON format.
- Generates downloadable Excel reports.

---

# 📚 API Summary

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/upload` | Upload Bill of Lading PDF |
| GET | `/api/bl-extract/{filename}` | Extract shipment information |
| GET | `/api/download/excel/{filename}` | Download Excel report |
| GET | `/api/download/json/{filename}` | Download JSON report |