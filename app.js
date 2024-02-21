document.addEventListener("DOMContentLoaded", () => {
  // Fetch uploaded images on page load
  fetch("/generate_csv")
    .then((response) => response.text())
    .then((csvData) => {
      const imageTable = document.createElement("table");
      imageTable.classList.add("table", "table-striped");

      // Create table header
      const headerRow = document.createElement("tr");
      const filenameHeader = document.createElement("th");
      filenameHeader.textContent = "Filename";
      const downloadHeader = document.createElement("th");
      downloadHeader.textContent = "Download";
      headerRow.appendChild(filenameHeader);
      headerRow.appendChild(downloadHeader);
      imageTable.appendChild(headerRow);

      // Parse CSV data and populate table
      const rows = csvData.trim().split("\n");
      rows.forEach((row) => {
        const [filename, downloadUrl] = row.split(",");
        const rowElement = document.createElement("tr");
        const filenameCell = document.createElement("td");
        filenameCell.textContent = filename;
        const downloadCell = document.createElement("td");
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.textContent = "Download";
        link.classList.add("btn", "btn-primary", "btn-sm");
        downloadCell.appendChild(link);
        rowElement.appendChild(filenameCell);
        rowElement.appendChild(downloadCell);
        imageTable.appendChild(rowElement);
      });

      // Add table to the DOM
      const imageList = document.getElementById("image-list");
      imageList.appendChild(imageTable);
    });

  // Update image list on successful upload
  document
    .getElementById("uploadForm")
    .addEventListener("submit", async (event) => {
      event.preventDefault();

      const formData = new FormData(event.target);

      try {
        const response = await fetch("/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Upload failed");
        }

        // Clear any existing error message
        document.getElementById("error-message").textContent = "";

        // Refresh image list
        window.location.reload();
      } catch (error) {
        console.error("Error uploading file:", error);
        document.getElementById("error-message").textContent = "Upload failed";
      }
    });

  // Display error message
  const errorMessageElement = document.getElementById("error-message");
  // ... (fetch error message from response or backend)
  // ... (display error message)
});
