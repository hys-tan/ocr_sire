"""
Utilities for handling comprobante identifiers (serie and numero).

Provides a helper to obtain a combined 'serie-numero' string from
fields that may be dicts (with 'valor') or raw strings/ints.

Behavior:
- Tolerant: if only one of serie/numero exists, returns the available one.
- Applies optional zero-padding to numero when pad_length is provided.
"""

from typing import Any, Optional


def _extract_val(field: Any) -> Optional[str]:
    if field is None:
        return None
    if isinstance(field, dict):
        v = field.get("valor")
    else:
        v = field
    if v is None:
        return None
    return str(v).strip()


def get_serie_numero(serie_field: Any, numero_field: Any, sep: str = '-') -> Optional[str]:
    """Return a combined serie-numero string.

    This function is intentionally conservative: it preserves the exact
    extracted values (no padding or mutation). If both serie and numero
    are present it returns "SERIE-SEPARADOR-NUMERO" with serie uppercased.
    If only one exists it returns that one. Returns None if none exist.
    """
    s = _extract_val(serie_field)
    n = _extract_val(numero_field)

    if s:
        s = s.upper()

    if s and n:
        return f"{s}{sep}{n}"
    return s or n or None


def validate_serie_numero(serie_field: Any, numero_field: Any, min_num_len: Optional[int] = None, max_num_len: Optional[int] = None) -> dict:
    """Validate serie/numero and return issues.

    Returns a dict with:
      - flagged: bool
      - issues: list[str]
      - severity: int (suggested confidence penalty magnitude)
    """
    issues = []
    severity = 0
    flagged = False

    n = _extract_val(numero_field)
    if n:
        # If numeric, check length boundaries
        if n.isdigit():
            ln = len(n)
            if min_num_len is not None and ln < min_num_len:
                flagged = True
                issues.append(f"numero demasiado corto: {ln} < {min_num_len}")
                severity = max(severity, 30)
            if max_num_len is not None and ln > max_num_len:
                flagged = True
                issues.append(f"numero demasiado largo: {ln} > {max_num_len}")
                severity = max(severity, 10)
        else:
            # numero contiene caracteres no numéricos — posible OCR confuso
            flagged = True
            issues.append("numero contiene caracteres no numéricos")
            severity = max(severity, 20)
    else:
        # Sin número, no necesariamente un error, solo registrar
        issues.append("numero no presente")

    s = _extract_val(serie_field)
    if not s:
        issues.append("serie no presente")

    return {"flagged": flagged, "issues": issues, "severity": severity}


def build_and_set_serie_numero(comprobante: dict, sep: str = '-', validate: bool = False, min_num_len: Optional[int] = None, max_num_len: Optional[int] = None, adjust_confidence: bool = False, penalty: int = 20) -> None:
    """Build serie_numero and optionally validate and adjust confidence.

    Args:
        comprobante: dict representing comprobante (mutated in-place)
        sep: separator between serie and numero
        validate: if True run validate_serie_numero and store issues
        min_num_len, max_num_len: bounds for numero length validation
        adjust_confidence: if True and validation flags issues, reduce 'score' on serie/numero fields by penalty
        penalty: integer amount to subtract from score when adjusting
    """
    serie = comprobante.get('serie')
    numero = comprobante.get('numero')
    serie_numero = get_serie_numero(serie, numero, sep=sep)
    if serie_numero is not None:
        comprobante['serie_numero'] = serie_numero

    if validate:
        result = validate_serie_numero(serie, numero, min_num_len=min_num_len, max_num_len=max_num_len)
        comprobante['serie_numero_issues'] = result['issues']
        comprobante['serie_numero_flagged'] = result['flagged']

        if adjust_confidence and result['flagged']:
            # Adjust scores defensively if fields exist and are dicts with 'score'
            for key in ('serie', 'numero'):
                field = comprobante.get(key)
                if isinstance(field, dict) and isinstance(field.get('score'), (int, float)):
                    old = int(field.get('score', 0))
                    new = max(0, old - penalty)
                    field['score'] = new
                    # Update textual confianza based on thresholds
                    if new >= 80:
                        field['confianza'] = 'ALTA'
                    elif new >= 50:
                        field['confianza'] = 'MEDIA'
                    else:
                        field['confianza'] = 'BAJA'
