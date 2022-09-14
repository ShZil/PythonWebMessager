function createModal(button, modal) {
    var close = modal.getElementsByClassName("close")[0];

    if (button != undefined) button.onclick = () => modal.style.display = "block";
    
    close.addEventListener("click", () => modal.style.display = "none");
      
    window.onclick = (event) => {if (event.target == modal) modal.style.display = "none"};
}