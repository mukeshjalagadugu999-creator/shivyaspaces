// PROPERTY IMAGE GALLERY

const mainImage = document.getElementById("mainPropertyImage");

const thumbnails = document.querySelectorAll(".thumb");

thumbnails.forEach((thumb) => {

  thumb.addEventListener("click", () => {

    // Change main image
    mainImage.src = thumb.src;

    // Remove active class from all
    thumbnails.forEach((item) => {
      item.classList.remove("active-thumb");
    });

    // Add active class to clicked image
    thumb.classList.add("active-thumb");

  });

});