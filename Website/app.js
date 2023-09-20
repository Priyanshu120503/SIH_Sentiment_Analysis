//jshint esversion:6

const express = require("express");
const bodyParser = require("body-parser");
const ejs = require("ejs");

const https = require("https");

const app = express();


app.set('view engine', 'ejs');

app.use(bodyParser.urlencoded({extended: true}));
app.use(express.static("public"));

app.get("/", function(req, res){
  res.render("home");
});

app.get("/view", function(req, res){
  res.render("view");
});

app.get("/register", function(req, res){
  res.render("register");
});

app.get("/login", function(req, res){
  res.render("login")
});

app.post("/data", function(req, res){
  const object = {
    level : req.body.site,
    link : req.body.link
  }
  console.log(object);
  res.render("view",{
    variable : object
  })
});


app.listen(3000, function() {
  console.log("Server started on port 3000 boi");
});

