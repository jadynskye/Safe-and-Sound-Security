// scripts/login.js

// wrap everything in an IIFE 
// why? it runs right away when the page loads
(async function() {

  // grab the form and input elements from the page
  const form    = document.querySelector("form");
  const emailEl = document.getElementById("email");
  const passEl  = document.getElementById("password");


  // form is submitted = run this code instead of reloading the page
  form.addEventListener("submit", async (e) => {
    // stop the normal form submit
    e.preventDefault();   


    // send login info to the backend API
    const res = await fetch("http://127.0.0.1:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: emailEl.value,
        password: passEl.value
      })
    });


    // if login fails return alert
    if (!res.ok) {
      alert("Invalid login");
      return;
    }


    // login works =  get the data back
    // ok: true, token: "demo-1"
    const data = await res.json();


    // save the token to localStorage
    localStorage.setItem("ss_token", data.token);


    // go to  dashboard page ! and hope this all works lol
    window.location.href = "dashboard.html";
  });

})();