document.addEventListener("DOMContentLoaded", () => {
  /* ---------- INDEX PAGE ---------- */

  // Get a Quote -> upload page
  const quoteBtn = document.getElementById("get-quote");
  if (quoteBtn) {
    quoteBtn.addEventListener("click", () => {
      window.location.href = "upload.html";
    });
  }

  // Contact Us -> footer at the bottom
  const contactBtn = document.getElementById("contact-btn");
  const contactSection = document.getElementById("contact");
  if (contactBtn && contactSection) {
    contactBtn.addEventListener("click", () => {
      contactSection.scrollIntoView({ behavior: "smooth" });
    });
  }

  // About -> "How It Works"
  const aboutLink = document.getElementById("about-link");
  const howItWorks = document.getElementById("featured-3");
  if (aboutLink && howItWorks) {
    aboutLink.addEventListener("click", (e) => {
      e.preventDefault();
      howItWorks.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Carousel auto-play (only if Bootstrap and the carousel exist)
  const carouselEl = document.getElementById("carouselExampleIndicators");
  if (carouselEl && typeof bootstrap !== "undefined") {
    new bootstrap.Carousel(carouselEl, {
      interval: 4000,
      ride: "carousel",
      pause: "hover",
    });
  }

  // Footer year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- UPLOAD PAGE ---------- */

  const uploadButton = document.getElementById("upload-button");
  const uploadBox = document.querySelector(".container");
  const error = document.getElementById("error");
  const imageDisplay = document.getElementById("image-display");

  if (uploadButton && uploadBox && error && imageDisplay) {
    const fileHandler = (file, name, type) => {
      if (type.split("/")[0] !== "image") {
        error.innerText = "Please upload an image file";
        return false;
      }
      error.innerText = "";
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onloadend = () => {
        const imageContainer = document.createElement("figure");
        const img = document.createElement("img");
        img.src = reader.result;
        imageContainer.appendChild(img);
        imageContainer.innerHTML += `<figcaption>${name}</figcaption>`;
        imageDisplay.appendChild(imageContainer);
      };
    };

    // Upload button
    uploadButton.addEventListener("change", () => {
      imageDisplay.innerHTML = "";
      Array.from(uploadButton.files).forEach((file) => {
        fileHandler(file, file.name, file.type);
      });
    });

    // Drag and drop
    ["dragenter", "dragover"].forEach((evt) => {
      uploadBox.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadBox.classList.add("active");
      });
    });

    uploadBox.addEventListener("dragleave", (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove("active");
    });

    uploadBox.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove("active");
      imageDisplay.innerHTML = "";
      Array.from(e.dataTransfer.files).forEach((file) => {
        fileHandler(file, file.name, file.type);
      });
    });

    error.innerText = "";
  }
});