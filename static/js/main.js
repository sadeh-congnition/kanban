// Main Javascript file

// Initialize SortableJS when HTMX loads content
document.body.addEventListener('htmx:afterSwap', function (evt) {
    if (evt.detail.target.id === 'board-canvas') {
        initDragAndDrop();
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Check if board-canvas is in DOM initially (might be loaded later by htmx, but just in case)
    const board = document.getElementById('board-canvas');
    if (board && board.children.length > 0) {
        initDragAndDrop();
    }
});

function initDragAndDrop() {
    // 1. Initialize Columns Sortable (horizontal drag-and-drop for columns)
    const boardCanvas = document.getElementById('board-canvas');
    if (boardCanvas) {
        new Sortable(boardCanvas, {
            group: 'columns',
            animation: 150,
            handle: '.column-header', // drag by column header
            filter: '.btn, button, input, textarea, a',
            preventOnFilter: false,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: function (evt) {
                const itemEl = evt.item;
                const columnId = itemEl.dataset.columnId;
                const newIndex = evt.newIndex;

                if (evt.oldIndex !== evt.newIndex) {
                    // Make API call to reorder column using HTMX ajax or fetch
                    htmx.ajax('POST', `/api/columns/${columnId}/move`, {
                        values: { new_order: newIndex },
                        swap: 'none'
                    });
                }
            },
        });
    }

    // 2. Initialize Tasks Sortable (vertical drag-and-drop between columns)
    const columnBodies = document.querySelectorAll('.column-body');
    columnBodies.forEach(col => {
        new Sortable(col, {
            group: 'tasks',
            animation: 150,
            filter: '.btn, button, input, textarea, a',
            preventOnFilter: false,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: function (evt) {
                const itemEl = evt.item;
                const taskId = itemEl.dataset.taskId;
                const toList = evt.to;

                const newColumnId = toList.closest('.column').dataset.columnId;
                const newIndex = evt.newIndex;
                const oldIndex = evt.oldIndex;
                const oldColumnId = evt.from.closest('.column').dataset.columnId;

                if (oldIndex !== newIndex || oldColumnId !== newColumnId) {
                    // Make API call to move task
                    htmx.ajax('POST', `/api/tasks/${taskId}/move`, {
                        values: {
                            new_column_id: newColumnId,
                            new_order: newIndex
                        },
                        swap: 'none'
                    });
                }
            },
        });
    });
}

// Function to close modal explicitly if needed
function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

// Listen for custom event to close modal after successful submission
document.body.addEventListener('closeModal', function () {
    closeModal();
});
