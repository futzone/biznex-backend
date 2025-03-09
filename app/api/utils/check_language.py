from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from app.api.constants.languages import languages, languages_error_message


async def check_language(language: str):
    if language is None:
        return
    if language not in languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=languages_error_message,
        )


def update_language_dict(
    existing_dict: Optional[Dict[str, str]],
    new_values: Dict[str, str],
) -> Dict[str, str]:
    if existing_dict is None:
        existing_dict = {}

    for key in new_values.keys():
        if key not in languages:
            pass
    existing_dict.update(new_values)
    return existing_dict
