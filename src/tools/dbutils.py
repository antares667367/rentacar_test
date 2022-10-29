from hashlib import sha1


def pass_auth(user: str, password: str, db) -> bool:
    """pass auth
    Args:
        user (str): username to look for
        password (str): password associated

    Returns:
        bool: True,user if user exists else False,None
    """
    getusers = db.get_by_query(
        lambda x: x["skey"] == sha1("".join([user, password]).encode()).hexdigest()
    )
    ln = len(getusers)

    if ln > 0:
        res = [v for _, v in getusers.items()]
        return (ln > 0), res[0]
    return False, None
