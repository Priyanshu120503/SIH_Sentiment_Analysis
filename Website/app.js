//jshint esversion:6

const express = require("express");
const bodyParser = require("body-parser");
const ejs = require("ejs");
const Razorpay = require("razorpay")

const https = require("https");

const app = express();


app.set("view engine", "ejs");
app.set("views", __dirname + "\\views")
app.use(bodyParser.urlencoded({extended: true}));
app.use(express.static(__dirname + "\\public"));

app.get("/", function(req, res){
  res.render("home");
});

app.get("/view", function(req, res){
  res.render("view");
});

app.get("/register", function(req, res){
  res.render("register");
});

app.post("/", async function(req, res){
  const object = {
    level : req.body.site,
    link : req.body.link
  }
  console.log(object);
  console.log("http://127.0.0.1:5000/data/" + encodeURIComponent(object.link));
  result = await fetch("http://127.0.0.1:5000/data/" + encodeURIComponent(object.link), {
    method: "GET"
  }).then(res => res.json()).then(data => data);
  
  console.log(result);
  
  res.render("view",{
    variable : object,
    data: result
  })
});


app.listen(3000, function() {
  console.log("Server started on port 3000 boi");
});


// appid 
// 5058447

// api key
// 7e98973274msh649245247ddbf5ap17f005jsn76349966ce4b