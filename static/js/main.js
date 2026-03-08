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

// HTMX event listeners for error handling
document.body.addEventListener('htmx:responseError', function(evt) {
    // Check if this is a task move request
    if (evt.detail.requestConfig && evt.detail.requestConfig.path && evt.detail.requestConfig.path.includes('/tasks/') && evt.detail.requestConfig.path.includes('/move')) {
        showErrorMessage(evt.detail.xhr.responseText || 'Failed to move task');
        // Revert the move in the UI by triggering a board refresh
        htmx.trigger(document.body, 'columnUpdated');
    }
});

// Function to show error messages to the user
function showErrorMessage(message) {
    // Create or update error toast
    let errorToast = document.getElementById('error-toast');
    if (!errorToast) {
        errorToast = document.createElement('div');
        errorToast.id = 'error-toast';
        errorToast.className = 'fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 max-w-md cursor-pointer transition-all duration-300';
        errorToast.style.cssText = `
            background: var(--danger-color);
            color: var(--text-primary);
            border: 1px solid var(--danger-hover);
            font-family: var(--font-body);
            font-size: 0.875rem;
            box-shadow: var(--shadow-lg);
        `;
        document.body.appendChild(errorToast);
    }
    
    errorToast.textContent = message;
    errorToast.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorToast.style.display = 'none';
    }, 5000);
    
    // Allow clicking to dismiss
    errorToast.onclick = function() {
        errorToast.style.display = 'none';
    };
}
