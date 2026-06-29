# Como rodar

Este documento descreve, passo a passo, como reproduzir o ambiente, gerar os dois mapas (Hector SLAM e Gmapping), executar o AMCL sobre cada um deles e recalcular as métricas. Para a explicação dos resultados e a discussão, veja o [`README.md`](README.md).

## Estrutura do repositório

```
launch/
  lar_world.launch       -- sobe apenas o mundo do LaR no Gazebo
  lar_husky.launch       -- sobe Gazebo + Husky (opcionalmente com hector_slam:=true)
  hector_slam.launch     -- SLAM com Hector
  gmapping.launch        -- SLAM com gmapping
  amcl.launch             -- AMCL + map_server, parametrizado por mapa (criado para esta atividade)
scripts/
  run_husky.sh
  entrar.sh               -- acessa o container em execução sem precisar do ID manualmente
  captura_poses.py        -- grava ground truth + pose AMCL em CSV (criado para esta atividade)
  calcular_metricas.py    -- calcula RMSE, erro final, orientação, estabilidade (criado para esta atividade)
maps/
  mapa_hector.pgm / .yaml
  mapa_gmapping.pgm / .yaml
resultados/
  poses_mapa_hector.csv
  poses_mapa_gmapping.csv
  erro_posicao_mapa_hector.csv
  erro_posicao_mapa_gmapping.csv
  erro_ao_longo_do_tempo.png
imagens/
  recortes e vistas gerais dos mapas usados na análise qualitativa do README
docker/
  Dockerfile.noetic
  entrypoint.sh
```

Os demais diretórios (`models/`, `worlds/`, `maps/lab_robotica_06mai2019.*`, `april_tags/`, `husky_urdf_extras/`, `husky_accessories.sh`, `config/hector_slam.rviz`) pertencem ao pacote base do laboratório, necessários para o `catkin build`/`roslaunch` funcionarem. Não foram alterados nesta atividade.

## Ambiente

- ROS Noetic + Gazebo Classic 11
- Robô: Husky UGV (laser frontal `/front/scan`)
- Execução via Docker (`docker-compose.yml` neste repositório)

## 1. Build da imagem Docker

```bash
docker compose build
```

## 2. Subir o ambiente

```bash
./scripts/run_husky.sh gui:=false
```

A GUI 3D do Gazebo fica desligada por padrão para evitar sobrecarga de CPU, que pode introduzir atraso entre o `/front/scan` e o `/clock` simulado e travar a publicação do `/map`. Use o RViz para navegação visual em vez da GUI do Gazebo.

## 3. Gerar os mapas

Em outro terminal, acesse o container:
```bash
./scripts/entrar.sh
```

**Gmapping:**
```bash
roslaunch lar_gazebo gmapping.launch
# em outro terminal:
rosrun teleop_twist_keyboard teleop_twist_keyboard.py cmd_vel:=/kb_teleop/cmd_vel
# ative o display "Map" no RViz desde o início da exploração, para acompanhar a cobertura em tempo real
rosrun map_server map_saver -f /ws/src/lar_gazebo/maps/mapa_gmapping
```

**Hector SLAM:**
```bash
./scripts/run_husky.sh gui:=false hector_slam:=true
# teleoperar e salvar mapa_hector da mesma forma
rosrun map_server map_saver -f /ws/src/lar_gazebo/maps/mapa_hector
```

Sobre o comando de teleoperação: use sempre `cmd_vel:=/kb_teleop/cmd_vel`, nunca `/husky_velocity_controller/cmd_vel` diretamente. O nó `/twist_mux` arbitra entre múltiplas fontes (teclado, joystick) e só ele publica na saída final do Husky. Publicar direto na saída cria dois publishers concorrentes no mesmo tópico, e o teclado simplesmente perde — o robô parece não responder mesmo sem nenhum erro nos logs.

## 4. Rodar o AMCL e capturar dados

Para cada mapa:
```bash
roslaunch lar_gazebo amcl.launch map_file:=/ws/src/lar_gazebo/maps/mapa_hector.yaml
```

No RViz, usar **2D Pose Estimate** (clique-arrastar-soltar, não um clique simples) para indicar a pose inicial real do robô.

Antes de capturar os dados, vale confirmar a calibração:
```bash
# pose real do robô no mundo (ground truth) -- ANTES do Pose Estimate
rostopic echo /gazebo/model_states -n 1
```
Anote `x`, `y` do modelo `husky`. Depois do Pose Estimate, confirme que a pose do AMCL está de fato próxima do ground truth:
```bash
rostopic echo /amcl_pose -n 1
```
A diferença deve ser de poucos centímetros. Se for da ordem de metros, o Pose Estimate foi feito no ponto errado do mapa — refaça antes de capturar (veja no README a seção Limitações sobre o que aconteceu nesta execução).

Capturando:
```bash
python3 scripts/captura_poses.py mapa_hector
# teleoperar cobrindo o ambiente; Ctrl+C na captura ao terminar
```

Repetir substituindo por `mapa_gmapping`, refazendo o 2D Pose Estimate (a pose anterior não vale para o novo mapa).

Para validar o CSV antes de aceitar os dados, o critério correto não é o percentual de linhas repetidas no arquivo todo — uma taxa de ~99% é esperada e normal, já que o ground truth (`/gazebo/model_states`) publica a ~100Hz enquanto o AMCL atualiza a ~0.9Hz (dado `update_min_d=0.2`, `update_min_a=0.2`). O que importa é a maior sequência contínua de repetição em segundos: valores na faixa de 1–4s são saudáveis, sequências de 10s ou mais indicam robô parado por algum problema operacional naquele trecho.

## 5. Calcular métricas

```bash
python3 scripts/calcular_metricas.py resultados/poses_mapa_hector.csv resultados/poses_mapa_gmapping.csv
```

Gera no terminal as métricas de cada execução e a comparação direta, além de:
- `erro_posicao_<mapa>.csv` — série temporal do erro
- `erro_ao_longo_do_tempo.png` — gráfico comparativo de erro de posição/orientação