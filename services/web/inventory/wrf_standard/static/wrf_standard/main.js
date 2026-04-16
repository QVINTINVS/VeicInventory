console.log("main.js is loaded");

function toggleStatusToPendingOf(aBadge) {
  aBadge.classList.remove('bg-danger');
  aBadge.classList.add('bg-warning');
  aBadge.dataset.status = 'pending';
}

const process_button = document.querySelector('.process-button')

if (process_button) {
  process_button.addEventListener('click', (e) => {
      const row = document.querySelector('#data-table tbody tr');

      if (!row) {
        console.warn('No data row found in #data-table');
        return;
      }

      const notProcessedBadge = row.querySelector(
        ".badge-transition[data-status='not-processed']"
      );

      if (!notProcessedBadge) {
        console.warn('No not-processed badge found in selected row');
        return;
      }

      toggleStatusToPendingOf(notProcessedBadge);

      console.log("Process button clicked, status set to pending");

      // Send AJAX request to backend
      fetch('/process_emission/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({})
      })
      .then(response => response.json())
      .then(data => {
        console.log('Backend response:', data);
      })
      .catch(error => {
        console.error('Error:', error);
      });
    });
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.process-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();

      setTimeout(() => form.submit(), 500);
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.delete-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();

      const row = form.closest('tr');
      row.classList.add('fade-out');

      setTimeout(() => form.submit(), 500);
    });
  })

  const modal = document.getElementById("visualizeModal");
  const iframe = document.getElementById("iframe");
  const iframeSrc = "/wrf-standard/visualize/";
  if (iframe) iframe.src = "";

  if (modal) {
    modal.addEventListener("shown.bs.modal", () => {
      iframe.src = iframeSrc
      console.log("iframe is shown")
    })

    modal.addEventListener("hidden.bs.modal", () => {
      iframe.src = ""
      console.log("iframe is hidden")
    })
  }

  const addButton = document.getElementById("add-data");
  const modalBody = document.getElementById("addModalBody");
  const modalTitle = document.getElementById('addModalLabel');

  if (!addButton || !modalBody || !modalTitle) return;

  addButton.addEventListener("click", () => {
    console.log("Fetching form...");

    modalTitle.textContent = 'Adicionar emissão WRF';

    // Reset loading state every time
    modalBody.innerHTML = "<div class='text-center text-muted'>Carregando…</div>";

    fetch("/wrf-standard/add/?modal=true")
      .then(response => {
        if (!response.ok) {
          throw new Error("HTTP " + response.status);
        }
        return response.text();
      })
      .then(html => {
        modalBody.innerHTML = html;
      })
      .catch(error => {
        console.error("Error loading modal:", error);
        modalBody.innerHTML =
          "<div class='text-danger text-center'>Erro ao carregar formulário</div>";
      });
  });

  // Edit button handler
  document.querySelectorAll('.edit-button').forEach((button) => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      const editUrl = button.getAttribute('data-edit-url');
      const modal = new bootstrap.Modal(document.getElementById('addModal'));

      modalTitle.textContent = 'Editar emissão WRF';

      modalBody.innerHTML = "<div class='text-center text-muted'>Carregando…</div>";

      fetch(editUrl + '?modal=true')
        .then(response => {
          if (!response.ok) {
            throw new Error("HTTP " + response.status);
          }
          return response.text();
        })
        .then(html => {
          modalBody.innerHTML = html;
        })
        .catch(error => {
          console.error("Error loading modal:", error);
          modalBody.innerHTML =
            "<div class='text-danger text-center'>Erro ao carregar formulário</div>";
        });

      modal.show();
    });
  });
});
