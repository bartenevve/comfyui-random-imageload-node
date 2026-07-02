# comfyui-random-image

`LoadRandomImage` — LoadImage-подобная нода с рандомным/последовательным выбором файла из произвольной директории.

## Установка (вручную / из архива)

1. Скопировать/распаковать папку `comfyui-random-image` в `<ComfyUI>/custom_nodes/`
2. Перезапустить ComfyUI
3. Нода появится в поиске как **Load Random Image 🎲** (категория `image`)

Зависимости — `torch`, `Pillow`, `aiohttp`, `numpy` — уже идут с ComfyUI, ставить отдельно не нужно.

## Установка через git

На машине с ComfyUI:

```bash
cd <ComfyUI>/custom_nodes
git clone <URL_твоего_репозитория> comfyui-random-image
```

Перезапустить ComfyUI.

Обновление в будущем:

```bash
cd <ComfyUI>/custom_nodes/comfyui-random-image
git pull
```

## Файлы

- `nodes.py` — backend-нода (`LoadRandomImage`)
- `routes.py` — aiohttp API: `/random_image/pick`, `/random_image/list`, `/random_image/view`, `/random_image/input_dir`
- `js/random_image.js` — frontend: dropdown файлов, кнопка рандома, drag&drop, живое превью
- `__init__.py` — регистрация ноды и `WEB_DIRECTORY`
