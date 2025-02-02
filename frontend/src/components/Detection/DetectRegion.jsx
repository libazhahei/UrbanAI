import React, { useState, useEffect, useRef, Suspense, useFrame } from 'react';
import * as THREE from 'three';
import { PLYLoader, OBJLoader } from 'three-stdlib';
import { useLoader } from '@react-three/fiber';
// import { OBJLoader } from 'three/addons/loaders/OBJLoader';

import { useThree, Canvas } from '@react-three/fiber';
// import { Group } from 'three';
// Custom vertex shader
// const 

const DetectRegion = ({ position, setLookAt, responseBody , isframe}) => {
  const [geo, setGeo] = useState('');
  const [minHeight, setMinHeight] = useState(Number.POSITIVE_INFINITY);
  const [maxHeight, setMaxHeight] = useState(Number.NEGATIVE_INFINITY);
  const [center, setCenter] = useState([0, 0, 0]);
  const [meshs,setMeshs] = useState([])
  const camera = useThree((state) => state.camera); // Access camera object
  // Create a ref to store the mesh material
  const materialRef = useRef();
  const frame = isframe === 'Yes' ? true : false;
  // console.log(responseBody.download_link);
  const groupRef = useRef();
    // THREE.Group()
// const group = useRef();

//   const obj = useLoader(OBJLoader, "class10.obj");

  useEffect(async () => {
    const loader = new OBJLoader();
    loader.load(
    //   "http://13.210.146.135:5000" + responseBody.download_link,
      // "http://127.0.0.1:9999" + responseBody.download_link,
      "class10.obj",
      function (geometry) {
        geometry.scale.set(1000, 1000, 1000);
        console.log(geometry);
        // console.log(position)
        // geometry.computeVertexNormals()
        // geometry.computeBoundingBox();
        // geometry.computeBoundingSphere();
        setLookAt([
            0,0,0
        ]);
        // setCenter([geometry.boundingSphere.center.x, geometry.boundingSphere.center.y, geometry.boundingSphere.center.z])
        // geometry.position.set(geometry.boundingSphere.center.x, geometry.boundingSphere.center.y, geometry.boundingSphere.center.z)
        // geometry.scene.position.sub(geometry.boundingSphere.center); // Center the geometry
        // geometry.needsUpdate = true;
        // console.log(geometry);
        // geometry.up = new THREE.Vector3(1, 0, 0);
        groupRef.current = geometry;
        // groupRef.current.add(geometry);
        setGeo(geometry);
        console.log("Log")
        for (let index = 0; index < groupRef.current.children.length; index++) {
            let child = groupRef.current.children[index];
            console.log(child)
            
            setMeshs([...meshs, child])
 
            
        }
        // groupRef.current.children.map((child, index) => (
        //     console.log(child)
        // ))
        console.log(groupRef);
        console.log(geometry)
        // rotate the geometry to the correct position
        // geometry.rotateX(-Math.PI / 2);
        // Set far property of the camera
        camera.far = 1000000; // Set a large value for far property
        camera.position.set(0,0,0);
        camera.updateProjectionMatrix(); // Apply changes to camera
      },
      function (xhr) {
        console.log((xhr.loaded / xhr.total) * 100 + "% loaded");
      },
      function (error) {
        console.log("An error happened");
        console.log(error);
      }
    );
  }, []);
  // Calculate min and max heights
//   useEffect(() => {
//     if (geo) {
//     //   const { min, max } = calculateMinMaxHeights();
//     //   setMinHeight(min);
//     //   setMaxHeight(max);
//         console.log(groupRef.current.children)  
//     }
//   }, [groupRef]);

  // Function to calculate min and max heights
  const calculateMinMaxHeights = () => {
    // const min = geo.boundingBox.min.z;
    // const max = geo.boundingBox.max.z;
    // return { 0, 0 };
  };

  // Update the uniform values in the material
  useEffect(() => {
    if (materialRef.current) {
      materialRef.current.uniforms.minHeight.value = minHeight;
      materialRef.current.uniforms.maxHeight.value = maxHeight;
    }
  }, [minHeight, maxHeight]);
//   const material = useRef();
//   useFrame(() => {
//     if (material.current) {
//       material.current.uniforms.minHeight.value = minHeight;
//       material.current.uniforms.maxHeight.value = maxHeight;
//     }
//   });

  return (
  //   <group ref={group}>
  //       <primitive object={obj} />
  // </group>
   
    // for (let index = 0; index < array.length; index++) {
    //     const element = array[index];
        
    // }
    // <mesh
    // {meshs.map((item, index))}
    
    // meshs.forEach(child => (
    //              <mesh
    //                     key={1}
    //                     position={[child.position.x, child.position.y, child.position.z]}
    //                     scale={[child.scale.x, child.scale.y, child.scale.z]}
    //                     rotation={[child.rotation.x, child.rotation.y, child.rotation.z]}
    //                 >
    //                  {/* Use appropriate geometry and material for each child */}
    //                      <boxBufferGeometry args={[1, 1, 1]} />
    //                      <meshBasicMaterial color="blue" />
    //                 </mesh>
    //              ))
    
    // >
    // <group ref={groupRef}>
 // {/* //          {geo.children.forEach(child => (
//          <mesh
//                 key={1}
//                 position={[child.position.x, child.position.y, child.position.z]}
//                 scale={[child.scale.x, child.scale.y, child.scale.z]}
//                 rotation={[child.rotation.x, child.rotation.y, child.rotation.z]}
//             >
//              {/* Use appropriate geometry and material for each child */}
// {/* //                  <boxBufferGeometry args={[1, 1, 1]} />
//                  <meshBasicMaterial color="blue" />
//             </mesh>
//          ))}; */}
    // </group>
//  */}

    // <mesh>
    //     <boxBufferGeometry args={[1, 1, 1]} />
    //     <meshStandardMaterial color="blue" />
    // </mesh>
        <group ref={groupRef}></group>
        // {/* Iterate over children and render each mesh */}
        // {groupRef.current &&
        //     groupRef.current.children.map((child, index) => (
        //     <mesh
        //         key={index}
        //         position={[child.position.x, child.position.y, child.position.z]}
        //         scale={[child.scale.x, child.scale.y, child.scale.z]}
        //         rotation={[child.rotation.x, child.rotation.y, child.rotation.z]}
        //     >
                
        //         {/* Use appropriate geometry and material for each child */}
        //         <boxBufferGeometry args={[1, 1, 1]} />
        //         <meshBasicMaterial color="blue" />
        //     </mesh>
        //     ))}
        // </group>
 
    // <Canvas>
    //     <group ref={groupRef}>
    //         {/* Use the react-three-fiber primitive components to render the three.js object */}
    //         <mesh position={[0, 0, 0]} scale={[1, 1, 1]} ref={groupRef}>
    //         <boxBufferGeometry args={[1, 1, 1]} />
    //         <meshBasicMaterial color="red" />
    //         </mesh>

    //         {/* Render the children of the geometry object */}
    //         {geo.children.map((child, index) => (
    //         <mesh
    //             key={index}
    //             position={[child.position.x, child.position.y, child.position.z]}
    //             scale={[child.scale.x, child.scale.y, child.scale.z]}
    //             rotation={[child.rotation.x, child.rotation.y, child.rotation.z]}
    //         >
    //             {/* Use appropriate geometry and material for each child */}
    //             <boxBufferGeometry args={[1, 1, 1]} />
    //             <meshBasicMaterial color="blue" />
    //         </mesh>
    //         ))}
    //     </group>
    // </Canvas>
    //   <shaderMaterial
    //     vertexShader={vertexShader}
    //     fragmentShader={fragmentShader}
    //     wireframe={frame}
    //     side={THREE.DoubleSide}
    //     uniforms={{
    //       minHeight: { value: minHeight },
    //       maxHeight: { value: maxHeight },
    //     }}
    //     // uniformsNeedUpdate = {true}
    //   />
      
  );
};

export default DetectRegion;