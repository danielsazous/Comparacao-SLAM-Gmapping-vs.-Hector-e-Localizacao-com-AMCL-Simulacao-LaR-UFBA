#!/usr/bin/env python3
"""
gerar_imagens_mapas.py

Gera, a partir de maps/mapa_hector.pgm e maps/mapa_gmapping.pgm, as imagens
usadas na análise qualitativa do README.md:

  imagens/mapa_hector_overview.png
  imagens/mapa_gmapping_overview.png
  imagens/detalhe_regiao_desconhecida_hector.png
  imagens/detalhe_regiao_desconhecida_gmapping.png
  imagens/detalhe_objetos_hector.png
  imagens/detalhe_objetos_gmapping.png
  imagens/detalhe_parede_hector.png
  imagens/detalhe_parede_gmapping.png

Uso (a partir da raiz do repositório):
    pip3 install pillow numpy --break-system-packages
    python3 scripts/gerar_imagens_mapas.py

IMPORTANTE: as caixas de recorte dos "detalhes" (DETALHES_HECTOR / DETALHES_GMAPPING
abaixo) foram ajustadas manualmente olhando para ESTES mapas específicos. Se você
gerar novos mapas (nova exploração, outra área coberta), essas coordenadas vão
mudar -- abra mapa_hector_overview.png / mapa_gmapping_overview.png, veja em que
pixel cada elemento de interesse aparece (a maioria dos visualizadores de imagem
mostra a posição do cursor), e ajuste os valores de (x0, y0, x1, y1) nesta seção.
"""

import os
import numpy as np
from PIL import Image



PASTA_MAPS = "slamlocalizacao/maps"
PASTA_SAIDA = "imagens"
ESCALA_OVERVIEW = 3   # zoom da vista geral
ESCALA_DETALHE = 6    # zoom dos recortes de detalhe
MARGEM_OVERVIEW = 4   # px de margem em torno da área conhecida do mapa

# Caixas de recorte (x0, y0, x1, y1) em pixels da imagem ORIGINAL do .pgm,
# encontradas inspecionando visualmente mapa_hector.pgm e mapa_gmapping.pgm.
DETALHES_HECTOR = {
    "regiao_desconhecida": (25, 55, 140, 140),
    "objetos":              (115, 150, 200, 185),
    "parede":               (55, 180, 200, 238),
}
DETALHES_GMAPPING = {
    "regiao_desconhecida": (900, 910, 1015, 995),
    "objetos":              (990, 1005, 1075, 1040),
    "parede":               (930, 1035, 1075, 1093),
}


def cor_unknown(arr):
    """Valor de cinza típico de 'desconhecido' no map_server (geralmente 205)."""
    valores, contagens = np.unique(arr, return_counts=True)
    # 'desconhecido' costuma ser o valor mais frequente fora de 0 (ocupado) e 254 (livre)
    candidatos = [(v, c) for v, c in zip(valores, contagens) if v not in (0, 254)]
    if not candidatos:
        return 205
    return max(candidatos, key=lambda vc: vc[1])[0]


def recortar_area_conhecida(img, margem=4):
    arr = np.array(img)
    fundo = cor_unknown(arr)
    ys, xs = np.where(arr != fundo)
    if len(xs) == 0:
        return img
    x0, x1 = max(0, xs.min() - margem), min(img.width, xs.max() + margem)
    y0, y1 = max(0, ys.min() - margem), min(img.height, ys.max() + margem)
    return img.crop((x0, y0, x1, y1))


def salvar_redimensionado(img, caminho, escala):
    out = img.resize((img.width * escala, img.height * escala), Image.NEAREST)
    out.save(caminho)
    print(f"  -> {caminho}  ({out.width}x{out.height})")


def gerar_overview(caminho_pgm, nome, pasta_saida):
    img = Image.open(caminho_pgm).convert("L")
    crop = recortar_area_conhecida(img, MARGEM_OVERVIEW)
    salvar_redimensionado(crop, os.path.join(pasta_saida, f"mapa_{nome}_overview.png"), ESCALA_OVERVIEW)


def gerar_detalhes(caminho_pgm, nome, caixas, pasta_saida):
    img = Image.open(caminho_pgm).convert("L")
    for rotulo, caixa in caixas.items():
        crop = img.crop(caixa)
        salvar_redimensionado(crop, os.path.join(pasta_saida, f"detalhe_{rotulo}_{nome}.png"), ESCALA_DETALHE)


def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    caminho_hector = os.path.join(PASTA_MAPS, "mapa_hector.pgm")
    caminho_gmapping = os.path.join(PASTA_MAPS, "mapa_gmapping.pgm")

    for caminho in (caminho_hector, caminho_gmapping):
        if not os.path.isfile(caminho):
            raise FileNotFoundError(
                f"Não encontrei {caminho}. Rode este script a partir da raiz do "
                f"repositório (onde está a pasta '{PASTA_MAPS}/')."
            )

    print("Gerando vistas gerais...")
    gerar_overview(caminho_hector, "hector", PASTA_SAIDA)
    gerar_overview(caminho_gmapping, "gmapping", PASTA_SAIDA)

    print("Gerando recortes de detalhe (Hector)...")
    gerar_detalhes(caminho_hector, "hector", DETALHES_HECTOR, PASTA_SAIDA)

    print("Gerando recortes de detalhe (Gmapping)...")
    gerar_detalhes(caminho_gmapping, "gmapping", DETALHES_GMAPPING, PASTA_SAIDA)

    print(f"\nPronto. Imagens salvas em '{PASTA_SAIDA}/'.")


if __name__ == "__main__":
    main()