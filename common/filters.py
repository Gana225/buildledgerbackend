from datetime import date

from rest_framework.exceptions import ValidationError


def get_date_range(request):

    date_value = request.query_params.get(
        "date"
    )

    start_date = request.query_params.get(
        "start_date"
    )

    end_date = request.query_params.get(
        "end_date"
    )

    if date_value:
        try:
            selected_date = date.fromisoformat(
                date_value
            )
        except ValueError:
            raise ValidationError({
                "date": "Invalid date. Use YYYY-MM-DD."
            })

        return selected_date, selected_date

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = date.fromisoformat(
                start_date
            )
        except ValueError:
            raise ValidationError({
                "start_date":
                    "Invalid date. Use YYYY-MM-DD."
            })

    if end_date:
        try:
            parsed_end = date.fromisoformat(
                end_date
            )
        except ValueError:
            raise ValidationError({
                "end_date":
                    "Invalid date. Use YYYY-MM-DD."
            })

    if (
        parsed_start
        and parsed_end
        and parsed_start > parsed_end
    ):
        raise ValidationError({
            "date_range":
                "start_date cannot be after end_date."
        })

    return parsed_start, parsed_end