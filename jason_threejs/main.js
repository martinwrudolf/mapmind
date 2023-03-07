import * as THREE from 'three';
import {FontLoader} from 'three/addons/loaders/FontLoader.js'
import {TextGeometry} from 'three/addons/geometries/TextGeometry.js'
import { Vector3 } from 'three';
// import CameraControls from 'camera-controls'

// https://stackoverflow.com/questions/13039589/rotate-the-camera-around-an-object-using-the-arrow-keys-in-three-js
// http://jsfiddle.net/HXms8/4/

// https://stackoverflow.com/questions/24690731/three-js-3d-models-as-hyperlink

// http://soledadpenades.com/articles/three-js-tutorials/object-picking/

// https://blog.hubspot.com/website/html-dropdown

// https://javascript.plainenglish.io/intro-to-raycasting-in-three-js-211ac4aae768

// https://sbcode.net/threejs/raycaster/

// https://stackoverflow.com/questions/1085801/get-selected-value-in-dropdown-list-using-javascript

// use this? https://github.com/yomotsu/camera-controls
// https://www.freecodecamp.org/news/here-is-the-most-popular-ways-to-make-an-http-request-in-javascript-954ce8c95aaa/


var theta = 0;
var phi = 90;
var dis = 20;

function computeNewCameraPostion() {
    camera.position.x = dis * Math.sin(phi * (Math.PI / 180)) * Math.sin(theta * (Math.PI / 180));
    camera.position.z = dis * Math.sin(phi * (Math.PI / 180)) * Math.cos(theta * (Math.PI / 180));
    camera.position.y = dis * Math.cos(phi * (Math.PI / 180));
    console.log(camera.position.x + " " + camera.position.y  + " "    + camera.position.z);
};

document.addEventListener("keydown", (event) => {
    if (event.key == "ArrowLeft") {
        theta -= 1;
        computeNewCameraPostion();
        camera.lookAt(0,0,0);
    }
    else if (event.key == "ArrowRight") {
        theta += 1;
        computeNewCameraPostion();
        camera.lookAt(0,0,0);
    }
});

// for zooming in and out, have zoom cap?
document.addEventListener("wheel", (event) => {
    camera.zoom += event.deltaY;
});

var div = document.getElementById("viewbox");
var searchtermbox = document.getElementById("searchterm");
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera( 75, div.clientWidth / div.clientHeight, 10, 6000);
const renderer = new THREE.WebGLRenderer();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
renderer.setSize(div.clientWidth, div.clientHeight );
div.appendChild(renderer.domElement);

// for centering, for now
const geometry = new THREE.BoxGeometry( 1, 1, 1 );
console.log(geometry);
const material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
const cube = new THREE.Mesh( geometry, material );
scene.add( cube );
console.log(cube);

computeNewCameraPostion();
camera.lookAt(0,0,0);

const loader = new FontLoader();
var meshes = [];
var list = [];

document.getElementById("submitbutton").addEventListener("click", (e) => {
    // extract input from search as an array of strings
    var searchBarInput = document.getElementById("searchbar").value;
    const searchBarArray = searchBarInput.split(", ")
    // convert search bar input into HTTP request (model endpoint for now)
    // sendSearchRequest("http://"+location.host+"/api/search", searchBarArray, parseResponse);
    let objects = [];
    for (let i = 0; i < searchBarArray.length; i++) {
        let pos = []
        for (let j = 0; j < 3; j++) {
            pos[j] = (Math.random() * 20) - 10;
        }
        const searchBarObject = {"string": searchBarArray[i], "pos":pos};
        objects[i] = searchBarObject;
        console.log(searchBarObject);
    }
    parseResponse(objects);
});

function sendSearchRequest(url, input, callback) {
    let httpReq = new XMLHttpRequest();
    // mock http request
    httpReq.onreadystatechange = function() {
        if (httpReq.readyState == 4) {
            callback(JSON.parse(httpReq.responseText));
        }
    };
    httpReq.open("GET", url);
    httpReq.setRequestHeader("Content-Type", "appilcation/json");
    httpReq.setRequestHeader("Accept", "appilcation/json");
    httpReq.send(JSON.stringify(input));
}

function parseResponse(objects) {
    // get objects and store in list
    list = objects;
    // load text
    loader.load('https://unpkg.com/three@0.138.3/examples/fonts/helvetiker_regular.typeface.json', generateText);
};

function generateText(font) {
    theta = 0;
    computeNewCameraPostion();
    camera.lookAt(0,0,0);
    // clear previously rendered text meshes
    for (let i = 0; i < meshes.length; i++) {
        scene.remove(meshes[i]);
    }
    for (let i = 0; i < list.length; i++) {
        const geometry = new TextGeometry(list[i].string, {
            font: font,
            size: 1,
            height: 1
        });
        // console.log(geometry);
        const textMesh = new THREE.Mesh(geometry);
        // add model endpoint assiocated with string, do we need?
        // textMesh.userData = {URL: "http://"+location.host+"/api/inspect/" + list[i].string}
        textMesh.position.x = list[i].pos[0];
        textMesh.position.y = list[i].pos[2];
        textMesh.position.z = list[i].pos[1];
        // textMesh.position.x = 0;
        // textMesh.position.y = 0;
        // textMesh.position.z = 0;
        // textMesh.position.z = 0;
        scene.add(textMesh);
        // console.log(textMesh);
        meshes[i] = textMesh;
        // textMesh.rotation.x = 0;
        // textMesh.rotation.y = 0;
        // textMesh.rotation.z = 0;
        textMesh.lookAt(camera.position);
    }
};

function onPointerMove( event ) {

	// calculate pointer position in normalized device coordinates
	// (-1 to +1) for both components

	pointer.x = ( event.clientX / div.clientWidth ) * 2 - 1;
	pointer.y = - ( event.clientY / div.clientHeight ) * 2 + 1;
    console.log(pointer.x + " " + pointer.y);

};


function sendInspectRequest(object) {
    console.log("in function");
    console.log(object.string);
    // var inspectReq = new XMLHttpRequest();
    // inspectReq.onreadystatechange = function() {
    //     if (httpReq.readyState == 4) {
            
    //     }
    // };
}

function animate() {
    raycaster.setFromCamera( pointer, camera );
    // calculate objects intersecting the picking ray
    const intersects = raycaster.intersectObjects( scene.children );
    // console.log(intersects);
    if (intersects.length > 0) {
        console.log("Ray detected hit!");
        sendInspectRequest(intersects[0].object);
    }
	requestAnimationFrame( animate );
	renderer.render( scene, camera );
};
window.addEventListener('pointermove', onPointerMove);
// window.requestAnimationFrame(animate);
animate();