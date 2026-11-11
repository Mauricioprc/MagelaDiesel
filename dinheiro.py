import re


def centavos_para_reais(centavos):
    """123456 -> '1.234,56'"""
    centavos = max(0, int(centavos or 0))
    reais, resto = divmod(centavos, 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"{inteiro},{resto:02d}"


def string_para_centavos(valor):
    """Converte o que veio do campo (já mascarado) para centavos.

    A máscara do formulário sempre representa o valor como dígitos puros
    (os 2 últimos são os centavos), então basta remover tudo que não for
    dígito e interpretar o resultado como inteiro.
    """
    digitos = re.sub(r"\D", "", valor or "")
    return int(digitos) if digitos else 0
