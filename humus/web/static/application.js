document.addEventListener("DOMContentLoaded", (loadEvent) => {
  console.log("loaded");
  let form = document.getElementById("form");
  let input = document.getElementById("text-input");
  let display = document.getElementById("text-display");
  form.addEventListener("submit", (submitEvent) => {
    console.log("submitted");
    input.value = display.innerText;
  });
});
