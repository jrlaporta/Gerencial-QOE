USERS = {
    "admin": {"senha": "admin123", "perfil": "admin"},
    "user": {"senha": "user123", "perfil": "user"}
}

def autenticar(usuario, senha):
    if usuario in USERS and USERS[usuario]["senha"] == senha:
        return USERS[usuario]["perfil"]
    return None
