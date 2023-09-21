// jshint esversion:6

const express = require("express");
const bodyParser = require("body-parser");
const ejs = require("ejs");


const app = express();

app.set("view engine", "ejs");
app.set("views", __dirname + "\\views");
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname + "\\public"));

app.get("/", function (req, res) {
  res.render("home");
});

app.get("/view", function (req, res) {
  res.render("view");
});

app.get("/register", function (req, res) {
  res.render("register");
});

app.get("/login", function (req, res) {
  res.render("login");
});

// Make the route handler async
app.post("/data", async function (req, res) {
  const object = {
    level: req.body.site,
    link: req.body.link,
  };

  try {
    // Use 'await' inside the 'async' function
    const response = await fetch("http://127.0.0.1:5000/data/" + encodeURIComponent(object.link), {
      method: "GET",
    });

    if (response.ok) {
      const result = await response.json();

      res.render("view", {
        variable: object,
        data: result,
      });
    } else {
      // Handle the case where the response is not OK
      res.status(500).send("Error fetching data from the server");
    }
  } catch (error) {
    // Handle any errors that occur during the fetch or rendering
    console.error(error);
    res.status(500).send("Error fetching data from the server");
  }
});

app.listen(3000, function () {
  console.log("Server started on port 3000 boi");
});
