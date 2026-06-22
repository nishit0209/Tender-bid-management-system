import os
import json
import base64
from django.conf import settings
import urllib.request
import urllib.error

def scan_document_with_gemini(file_path):
    """
    Calls the Gemini API via REST to analyze a document for authenticity.
    Returns a dict with 'confidence_score' and 'remarks'.
    """
    from decouple import config
    api_key = config("GEMINI_API_KEY", default="").strip()
    if not api_key:
        return {
            "confidence_score": None,
            "remarks": "Gemini API key not configured."
        }

    # Prepare file
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except Exception as e:
        return {
            "confidence_score": None,
            "remarks": f"Failed to read file for analysis: {str(e)}"
        }

    # Determine mime type
    ext = os.path.splitext(file_path)[1].lower()
    mime_type = "image/jpeg"
    if ext == ".png":
        mime_type = "image/png"
    elif ext == ".pdf":
        mime_type = "application/pdf"

    # Encode to base64
    b64_data = base64.b64encode(file_data).decode("utf-8")

    # API Endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    # Payload
    prompt = (
        "You are a forensic document examiner. Analyze this document for signs of forgery, "
        "tampering, or inconsistencies. Return ONLY a valid JSON object without any markdown wrapping. "
        "The JSON MUST have exactly two keys: 'confidence_score' (an integer from 0 to 100, where 100 is perfectly authentic and 0 is completely fake) "
        "and 'remarks' (a string explaining what you found suspicious or if it looks good)."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode("utf-8"))
        
        # Extract text from response
        candidates = response_data.get("candidates", [])
        if not candidates:
            return {"confidence_score": None, "remarks": "No response from Gemini."}
            
        text = candidates[0].get("content", {}).get("parts", [])[0].get("text", "{}")
        text = text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        
        # Parse JSON
        result = json.loads(text)
        return {
            "confidence_score": result.get("confidence_score", None),
            "remarks": result.get("remarks", "Analysis complete.")
        }
        
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"confidence_score": None, "remarks": f"API HTTP Error {e.code}: {err_body}"}
    except urllib.error.URLError as e:
        return {"confidence_score": None, "remarks": f"API Request failed: {e.reason}"}
    except Exception as e:
        return {"confidence_score": None, "remarks": f"Analysis parsing error: {str(e)}"}
