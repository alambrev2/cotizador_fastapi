/**
 * Global Notification System
 * Replaces native alert() and confirm() with SweetAlert2.
 */

// Inject custom styles for SweetAlert2 to match the desired UI
const swalStyle = document.createElement('style');
swalStyle.innerHTML = `
.swal-custom-popup {
    border-radius: 24px !important;
    padding: 2rem 1.5rem !important;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
}
.swal-custom-title {
    color: #1e293b !important;
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    margin-bottom: 0.5rem !important;
    font-family: inherit !important;
}
.swal-custom-text {
    color: #64748b !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
}
.swal-custom-icon.swal2-warning {
    border-color: #fef3c7 !important;
    background-color: #fef3c7 !important;
    color: #d97706 !important;
    width: 80px !important;
    height: 80px !important;
    margin: 0 auto 1.5rem auto !important;
}
.swal-custom-icon.swal2-warning .swal2-icon-content {
    color: #d97706 !important;
    font-size: 3rem !important;
    font-weight: 600 !important;
}
.swal-custom-actions {
    display: flex !important;
    width: 100% !important;
    gap: 12px !important;
    margin-top: 1.5rem !important;
    padding: 0 !important;
}
.swal-custom-confirm {
    background-color: #f59e0b !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 1.5rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    flex: 1 !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.3) !important;
}
.swal-custom-confirm:hover {
    background-color: #d97706 !important;
    transform: translateY(-1px);
}
.swal-custom-cancel {
    background-color: white !important;
    color: #334155 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 14px !important;
    padding: 0.85rem 1.5rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    flex: 1 !important;
    transition: all 0.2s !important;
}
.swal-custom-cancel:hover {
    background-color: #f8fafc !important;
    border-color: #94a3b8 !important;
}
`;
document.head.appendChild(swalStyle);

const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 4000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
});

window.showNotification = function(message, type = 'info') {
    Toast.fire({
        icon: type,
        title: message
    });
};

window.showSuccessNotification = function(message) {
    showNotification(message, 'success');
};

window.showErrorNotification = function(message) {
    showNotification(message, 'error');
};

// Override native alert globally
window.alert = function(message) {
    showNotification(message, 'info');
};

// A custom confirm that returns a Promise resolving to boolean
window.showConfirmDialog = function(message, title="¿Confirmar acción?", confirmText="Continuar") {
    return Swal.fire({
        title: title,
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: confirmText,
        cancelButtonText: 'Cancelar',
        reverseButtons: true, // Puts Cancel on left, Confirm on right
        customClass: {
            popup: 'swal-custom-popup',
            title: 'swal-custom-title',
            htmlContainer: 'swal-custom-text',
            actions: 'swal-custom-actions',
            confirmButton: 'swal-custom-confirm',
            cancelButton: 'swal-custom-cancel',
            icon: 'swal-custom-icon'
        },
        buttonsStyling: false
    }).then((result) => {
        return result.isConfirmed;
    });
};
