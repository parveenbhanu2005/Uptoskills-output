async function loadFlagged(){

const response =
await fetch("/api/flagged");

const data =
await response.json();

document.getElementById(
"output"
).innerHTML=
JSON.stringify(data,null,4);

}


async function loadMetrics(){

const response =
await fetch("/api/metrics");

const data =
await response.json();

document.getElementById(
"output"
).innerHTML=
JSON.stringify(data,null,4);

}