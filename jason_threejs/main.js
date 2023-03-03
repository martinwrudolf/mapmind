import * as THREE from 'three';
import {FontLoader} from 'three/addons/loaders/FontLoader.js'
import {TextGeometry} from 'three/addons/geometries/TextGeometry.js'
import { Vector3 } from 'three';
// import CameraControls from 'camera-controls'

// https://stackoverflow.com/questions/13039589/rotate-the-camera-around-an-object-using-the-arrow-keys-in-three-js
// http://jsfiddle.net/HXms8/4/

// use this? https://github.com/yomotsu/camera-controls
// https://www.freecodecamp.org/news/here-is-the-most-popular-ways-to-make-an-http-request-in-javascript-954ce8c95aaa/

const scene = new THREE.Scene();
var div = document.getElementById("viewbox")
const camera = new THREE.PerspectiveCamera( 75, div.clientWidth / div.clientHeight, 10, 1000 );
const renderer = new THREE.WebGLRenderer();
renderer.setSize(div.clientWidth, div.clientHeight );
div.appendChild(renderer.domElement);
camera.position.set(0,20,0);
camera.lookAt(new Vector3(0,0,0));
const loader = new FontLoader();
var theta = 0;
var phi = 90;
var dis = 20;
function computeNewCameraPostion() {
    camera.position.x = dis * Math.sin(phi * (Math.PI / 180)) * Math.sin(theta * (Math.PI / 180));
    camera.position.z = dis * Math.sin(phi * (Math.PI / 180)) * Math.cos(theta * (Math.PI / 180));
    camera.position.y = dis * Math.cos(phi * (Math.PI / 180));
    console.log(camera.position.x + " " + camera.position.y  + " "    + camera.position.z);
}
document.addEventListener("keydown", (event) => {
    if (event.key == "ArrowLeft") {
        theta -= 1;
        computeNewCameraPostion();
        camera.lookAt(0,0,0);
        camera.rotation.z = Math.abs(camera.rotation.z)
        console.log(camera.rotation.x + " " + camera.rotation.y + " " + camera.position.z);
    }
    else if (event.key == "ArrowRight") {
        theta += 1;
        computeNewCameraPostion();
        camera.lookAt(0,0,0);
        camera.rotation.z = Math.abs(camera.rotation.z)
        console.log(camera.rotation.x + " " + camera.rotation.y + " " + camera.position.z);
    }
});
// for zooming in and out, have zoom cap?
document.addEventListener("wheel", (event) => {
    camera.zoom += event.deltaY;
})
var list = []
var meshes = []
document.getElementById("submitbutton").addEventListener("click", (e) => {
    list = []
    var searchBarInput = document.getElementById("searchbar").value;
    // convert search bar input into HTTP request
    const searchBarArray = searchBarInput.split(", ")
    for (let i = 0; i < searchBarArray.length; i++) {
        let pos = []
        for (let j = 0; j < 3; j++) {
            pos[j] = (Math.random() * 20) - 10;
        }
        const searchBarObject = {"string": searchBarArray[i], "pos":pos};
        list[i] = searchBarObject;
        console.log(searchBarObject);
    }
    loader.load('https://unpkg.com/three@0.138.3/examples/fonts/helvetiker_regular.typeface.json', generateText);
});
function animate() {
    requestAnimationFrame( animate );
    renderer.render( scene, camera );
}
animate();

function generateText(font) {
    // theta = 0;
    // computeNewCameraPostion();
    for (let i = 0; i < meshes.length; i++) {
        scene.remove(meshes[i]);
    }
    for (let i = 0; i < list.length; i++) {
        const geometry = new TextGeometry(list[i].string, {
            font: font,
            size: 1,
            height: 1
        });
        let textMesh = new THREE.Mesh(geometry);
        scene.add(textMesh);
        console.log(textMesh);
        textMesh.position.x = list[i].pos[0];
        textMesh.position.y = list[i].pos[2];
        textMesh.position.z = list[i].pos[1];
        meshes[i] = textMesh;
        textMesh.lookAt(camera);
    }
}



