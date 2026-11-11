from dinheiro import centavos_para_reais, string_para_centavos


def test_centavos_para_reais_formata_milhar():
    assert centavos_para_reais(110000) == "1.100,00"


def test_centavos_para_reais_sem_milhar():
    assert centavos_para_reais(19100) == "191,00"


def test_centavos_para_reais_zero():
    assert centavos_para_reais(0) == "0,00"


def test_centavos_para_reais_negativo_vira_zero():
    assert centavos_para_reais(-500) == "0,00"


def test_string_para_centavos_formatada():
    assert string_para_centavos("1.100,00") == 110000


def test_string_para_centavos_so_digitos():
    # é exatamente assim que a máscara do formulário representa o valor:
    # os dois últimos dígitos digitados são sempre os centavos.
    assert string_para_centavos("19100") == 19100


def test_string_para_centavos_vazia():
    assert string_para_centavos("") == 0
    assert string_para_centavos(None) == 0
