## -*- Encoding: UTF-8 -*-

prochainid=0
def get_prochain_id():
    global prochainid
    prochainid+=1
    return f'id_{prochainid}'
def reset_prochain_id():
    """Réinitialise le compteur d'ID pour une nouvelle partie"""
    global prochainid
    prochainid = 0


if __name__ == '__main__':
    test()