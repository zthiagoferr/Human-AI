import re
import unicodedata

USUARIO_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")


def normalizar_nome(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", nome)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = " ".join(texto.split())
    return texto.casefold()


def nome_valido(nome: str) -> bool:
    if not 3 <= len(nome) <= 80:
        return False
    if not any(caractere.isalpha() for caractere in nome):
        return False
    return all(
        caractere.isalpha() or caractere in " '.-"
        for caractere in nome
    )


def normalizar_usuario(usuario: str) -> str:
    return usuario.strip().lower()


def usuario_valido(usuario: str) -> bool:
    return bool(USUARIO_RE.fullmatch(usuario))


def senha_valida(senha: str) -> bool:
    if not 8 <= len(senha) <= 128:
        return False
    tem_letra = any(caractere.isalpha() for caractere in senha)
    tem_digito = any(caractere.isdigit() for caractere in senha)
    return tem_letra and tem_digito
