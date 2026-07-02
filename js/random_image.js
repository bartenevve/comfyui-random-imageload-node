import { app } from "../../scripts/app.js";

const NODE_NAME = "LoadRandomImage";

app.registerExtension({
    name: "comfyui.random_image",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
            const node = this;

            const dirWidget = node.widgets.find((w) => w.name === "directory");
            const filenameWidget = node.widgets.find((w) => w.name === "filename");
            const randomWidget = node.widgets.find((w) => w.name === "randomize_on_queue");
            const sequentialWidget = node.widgets.find((w) => w.name === "sequential_on_queue");

            // turn the plain STRING widget into a dropdown of files found
            // in `directory`, same idea as core LoadImage's file combo
            filenameWidget.type = "combo";
            filenameWidget.options = filenameWidget.options || {};
            filenameWidget.options.values = [];

            const img = document.createElement("img");
            img.style.width = "100%";
            img.style.objectFit = "contain";
            node.addDOMWidget("random_image_preview", "preview", img, { serialize: false });

            node.updateRandomImagePreview = function (filename) {
                if (!filename || !dirWidget.value) return;
                img.src =
                    "/random_image/view?dir=" + encodeURIComponent(dirWidget.value) +
                    "&filename=" + encodeURIComponent(filename) +
                    "&t=" + Date.now();
            };

            async function refreshFileList() {
                if (!dirWidget.value) {
                    filenameWidget.options.values = [];
                    return;
                }
                try {
                    const resp = await fetch("/random_image/list?dir=" + encodeURIComponent(dirWidget.value));
                    const data = await resp.json();
                    if (data.error) {
                        console.error("random_image list error:", data.error);
                        filenameWidget.options.values = [];
                        return;
                    }
                    filenameWidget.options.values = data.files || [];
                    if (!filenameWidget.options.values.includes(filenameWidget.value)) {
                        filenameWidget.value = filenameWidget.options.values[0] || "";
                    }
                    app.graph.setDirtyCanvas(true, true);
                } catch (e) {
                    console.error("random_image list failed:", e);
                }
            }

            function updateWidgetVisibility() {
                const auto = randomWidget.value || sequentialWidget.value;
                diceWidget.disabled = auto;
                filenameWidget.disabled = auto;
            }

            function makeMutuallyExclusive(source, other) {
                const origCallback = source.callback;
                source.callback = function (value) {
                    if (value && other.value) {
                        other.value = false;
                    }
                    updateWidgetVisibility();
                    return origCallback ? origCallback.apply(this, arguments) : undefined;
                };
            }
            makeMutuallyExclusive(randomWidget, sequentialWidget);
            makeMutuallyExclusive(sequentialWidget, randomWidget);

            const origFilenameCallback = filenameWidget.callback;
            filenameWidget.callback = function (value) {
                node.updateRandomImagePreview(value);
                return origFilenameCallback ? origFilenameCallback.apply(this, arguments) : undefined;
            };

            const origDirCallback = dirWidget.callback;
            dirWidget.callback = function (value) {
                refreshFileList();
                return origDirCallback ? origDirCallback.apply(this, arguments) : undefined;
            };

            const diceWidget = node.addWidget("button", "🎲 Randomize", null, async () => {
                if (!dirWidget.value) return;
                try {
                    const resp = await fetch("/random_image/pick?dir=" + encodeURIComponent(dirWidget.value));
                    const data = await resp.json();
                    if (data.error) {
                        console.error("random_image pick error:", data.error);
                        return;
                    }
                    if (!filenameWidget.options.values.includes(data.filename)) {
                        filenameWidget.options.values.push(data.filename);
                    }
                    filenameWidget.value = data.filename;
                    node.updateRandomImagePreview(data.filename);
                } catch (e) {
                    console.error("random_image pick failed:", e);
                }
            });

            async function uploadFile(file) {
                try {
                    const body = new FormData();
                    body.append("image", file);
                    const resp = await fetch("/upload/image", { method: "POST", body });
                    if (resp.status !== 200) {
                        console.error("random_image upload failed:", resp.status, resp.statusText);
                        return;
                    }
                    const data = await resp.json();

                    const dirResp = await fetch(
                        "/random_image/input_dir?subfolder=" + encodeURIComponent(data.subfolder || "")
                    );
                    const dirData = await dirResp.json();

                    dirWidget.value = dirData.directory;
                    await refreshFileList();
                    if (!filenameWidget.options.values.includes(data.name)) {
                        filenameWidget.options.values.push(data.name);
                    }
                    filenameWidget.value = data.name;
                    node.updateRandomImagePreview(data.name);
                } catch (e) {
                    console.error("random_image upload failed:", e);
                }
            }

            // drop an image straight onto the node - uploads to ComfyUI's
            // managed input dir and selects it, same end result as LoadImage
            node.onDragOver = function (e) {
                if (e.dataTransfer && e.dataTransfer.items) {
                    return [...e.dataTransfer.items].some(
                        (i) => i.kind === "file" && i.type.startsWith("image/")
                    );
                }
                return false;
            };

            node.onDragDrop = function (e) {
                let handled = false;
                for (const file of e.dataTransfer.files) {
                    if (file.type.startsWith("image/")) {
                        uploadFile(file);
                        handled = true;
                    }
                }
                return handled;
            };

            updateWidgetVisibility();
            if (dirWidget.value) {
                refreshFileList();
            }
            if (filenameWidget.value) {
                node.updateRandomImagePreview(filenameWidget.value);
            }

            return result;
        };

        // after the node actually executes, sync the widget + preview to
        // whatever file really got loaded - regardless of which mode chose it
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            if (onExecuted) onExecuted.apply(this, arguments);
            if (!message) return;

            // seeds the widget for the NEXT run - not what this run loaded
            const nextFilename = message.filename && message.filename[0];
            if (nextFilename) {
                const filenameWidget = this.widgets.find((w) => w.name === "filename");
                if (filenameWidget) filenameWidget.value = nextFilename;
            }

            // what this run actually sent downstream - what the preview should show
            const lastLoaded = message.last_loaded && message.last_loaded[0];
            if (lastLoaded && this.updateRandomImagePreview) {
                this.updateRandomImagePreview(lastLoaded);
            }
        };
    },
});
