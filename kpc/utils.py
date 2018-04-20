def _filterable_params(qd):
    """
       Remove '[]' from querydict keys.
       These are url parameters from multi-value fields
       which have '[]' appended to the name value.
       Django forms need the raw name value.
    """
    qd_out = qd.copy()
    for key, value in qd_out.items():
        if key.endswith('[]'):
            qd_out.setlist(key[:-2], qd_out.pop(key))
    return qd_out
