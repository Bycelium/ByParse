// define default stylesheet
let defaultStylesheet =  [
	{
		selector: 'node',
		style: {
			'background-color': 'data(color)',
			'label': 'data(label)',
			'shape': 'round-rectangle', 
			'text-valign': 'center',
			'background-opacity': 0.8
		}
	},

	{
	selector: ':parent',
		style: {
			'background-opacity': 0.6,
			'background-color': 'data(color)',
			'border-color': '#000000',
			'border-width': 0,
			'shape': 'round-rectangle', 
			'text-valign': 'bottom'
		}
	},

	{
		selector: 'edge',
		style: {
			'curve-style': 'straight',
			'line-color': 'data(color)',
			'line-style': 'data(linestyle)'
		}
	},
	{
		'selector': 'edge[arrow]',
		'style': {
			'target-arrow-shape': 'data(arrow)',
			'target-arrow-color': 'data(color)',
		}
	},
	{
		selector: 'node:selected',
		style: {
			'background-color': '#33ff00',
			'border-color': '#22ee00'
		}
	},
	
	{
		selector: 'node.fixed',
		style: {
			'shape': 'diamond',
			'background-color': '#9D9696',
		}
	}, 
	
	{
		selector: 'node.fixed:selected',
		style: {
			'background-color': '#33ff00',
		}
	},
	
	{
		selector: 'node.alignment',
		style: {
			'shape': 'round-heptagon',
			'background-color': '#fef2d1',
		}
	}, 
	
	{
		selector: 'node.alignment:selected',
		style: {
			'background-color': '#33ff00',
		}
	},  

	{
		selector: 'node.relative',
		style: {
			'shape': 'rectangle',
			'background-color': '#fed3d1',
		}
	}, 
	
	{
		selector: 'node.relative:selected',
		style: {
			'background-color': '#33ff00',
		}
	},

	{
		selector: 'edge:selected',
		style: {
			'line-color': '#33ff00'
		}
	}                 
];

let sample1_constraints = {
	"fixedNodeConstraint": [
		{
			"nodeId": "f1",
			"position": {
				"x": -150,
				"y": -100
			}
		},
		{
			"nodeId": "f2",
			"position": {
				"x": -50,
				"y": -150
			}
		},
		{
			"nodeId": "f3",
			"position": {
				"x": 100,
				"y": 150
			}
		}
	]
};

// Adding Constraints
let constraintListTable = document.getElementById("constraintListTable");

// Clear logs table
let clearConstraintListTable = function() {
	if (constraintListTable.rows.length > 1) {
		let length = constraintListTable.rows.length;
		for (let i = 0; i < length - 1; i++) {
			constraintListTable.deleteRow(1);
		}
	}
};

let addToHistory = function( constraintType, nodeIds, constraintInfo) {
	
	let row = constraintListTable.insertRow();
	let cell4 = row.insertCell(0);
	let cell3 = row.insertCell(0);
	let cell2 = row.insertCell(0);
	let cell1 = row.insertCell(0);
	cell1.innerHTML = constraintType;
	
	if(constraintType == 'Fixed'){
		let label = (cy.getElementById(nodeIds[0]).css('label') ? cy.getElementById(nodeIds[0]).css('label') : nodeIds);
		if(label.length > 15)
			label = label.substring(0, 12).concat("...");
		cell2.innerHTML = label;
		cell3.innerHTML = "x: "+constraintInfo.x+" y: "+constraintInfo.y;
	}
	else{
		let nodeList = "";
		nodeIds.forEach(function(nodeId, index){
			let label = (cy.getElementById(nodeId).css('label') ? cy.getElementById(nodeId).css('label') : nodeId);
			if(label.length > 15)
				label = label.substring(0, 12).concat("...");      
			if(index == 0)
				nodeList += label;
			else
				nodeList += ' - ' + label;
		});
		cell2.innerHTML = nodeList;
		cell3.innerHTML = constraintInfo;
	}
	
	// needed for highlighting constrained nodes
	let instance = cy.viewUtilities({
		highlightStyles: [
			{ node: { 'background-color': '#da14ff', 'border-color': '#980eb2'}, edge: {} }
		]
	});

	let rowToHighlight = $('#constraintListTable').find('tr').eq(row.rowIndex);

	let collectionToHighlight = cy.collection();
	nodeIds.forEach(function(id){
		collectionToHighlight = collectionToHighlight.union(cy.getElementById(id));
	});

	// 'Delete' symbol
	let button = document.createElement('button');
	button.setAttribute('class','close');
	button.setAttribute('aria-label', 'Close');
	if(constraintType == 'Fixed')
		button.onclick = function(event){
			deleteRowElements(row, nodeIds);
			instance.removeHighlights(collectionToHighlight.nodes());
		};
	else
		button.onclick = function(event){
			deleteRowElements(row, nodeIds, constraintInfo);
			instance.removeHighlights(collectionToHighlight.nodes());
		};
	let xSymbol = document.createElement('span');
	xSymbol.setAttribute('aria-hidden', 'true');
	xSymbol.style.color = "red";
	xSymbol.innerHTML = '&times';
	button.appendChild(xSymbol);
	cell4.appendChild(button);
	
	rowToHighlight.hover(function() {
		instance.highlight(collectionToHighlight.nodes(), 0);
	}, function() {
		instance.removeHighlights(collectionToHighlight.nodes());
	});
};

let fillConstraintListTableFromConstraints = function () {
	if(constraints.fixedNodeConstraint){
		constraints.fixedNodeConstraint.forEach(function(constraint){
			addToHistory("Fixed", [constraint.nodeId], constraint.position);
		});    
	}
	if(constraints.alignmentConstraint){
		if(constraints.alignmentConstraint.vertical){
			constraints.alignmentConstraint.vertical.forEach(function(item){
				addToHistory("Alignment", item, 'vertical');
			});
		}
		if(constraints.alignmentConstraint.horizontal){
			constraints.alignmentConstraint.horizontal.forEach(function(item){
				addToHistory("Alignment", item, 'horizontal');
			});
		}    
	}
	if(constraints.relativePlacementConstraint){
		constraints.relativePlacementConstraint.forEach(function(constraint){
			if(constraint.left)
				addToHistory("Relative", [constraint.left, constraint.right], 'l-r - ' + (constraint.gap ? parseInt(constraint.gap) : parseInt(cy.getElementById(constraint.left).width()/2 + cy.getElementById(constraint.right).width()/2 + 50)));
			else
				addToHistory("Relative", [constraint.top, constraint.bottom], 't-b - ' + (constraint.gap ? parseInt(constraint.gap) : parseInt(cy.getElementById(constraint.top).height()/2 + cy.getElementById(constraint.bottom).height()/2 + 50)));
		});
		
	}
};

let cy = window.cy = cytoscape({
	container: document.getElementById('cy'),
	ready: function(){              
		this.nodes().forEach(function(node){
			let size = Math.random()*40+30;
			node.css("width", size);
			node.css("height", size);
		});

		let initialLayout = this.layout({name: 'fcose', step: 'all', animationEasing: 'ease-out'});
		initialLayout.pon('layoutstart').then(function( event ){
			constraints.fixedNodeConstraint = JSON.parse(JSON.stringify(sample1_constraints.fixedNodeConstraint));
			clearConstraintListTable();
			fillConstraintListTableFromConstraints(); 
		});
		initialLayout.run();     
	},
	layout: {name: 'preset'},
	style: defaultStylesheet,
	elements: {
		nodes: [],
		edges: []
	},
	wheelSensitivity: 0.3
});

let constraints = {
	fixedNodeConstraint: undefined,
	alignmentConstraint: undefined,
	relativePlacementConstraint: undefined
};

// Handle Menu ------------------------------------------

// Graph file input
document.getElementById("openFile").addEventListener("click", function () {
	document.getElementById("inputFile").click();
});

$("body").on("change", "#inputFile", function (e, fileObject) {
	let inputFile = this.files[0] || fileObject;

	if (inputFile) {
		let fileExtension = inputFile.name.split('.').pop();
		let r = new FileReader();
		r.onload = function (e) {
			cy.remove(cy.elements());
			let content = e.target.result;
			if (fileExtension == "graphml" || fileExtension == "xml") {
				cy.graphml({layoutBy: 'null'});
				cy.graphml(content);
			} else if (fileExtension == "json") {
				cy.json({elements: JSON.parse(content)});
			} else {
				var tsv = cy.tsv();
				tsv.importTo(content);
			}
		};
		r.addEventListener('loadend', function () {      
			onLoad();
			clearConstraintListTable();      
			constraints.fixedNodeConstraint = undefined;
			constraints.alignmentConstraint = undefined;
			constraints.relativePlacementConstraint = undefined;
			
			document.getElementById("nodeList").addEventListener("change", function(){
				document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
				document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
			});
			 
		});
		r.readAsText(inputFile);
	} else {
		alert("Failed to load file");
	}
	$("#inputFile").val(null);
});

$("body").on("change", "#inputConstraint", function (e, fileObject) {
	let inputFile = this.files[0] || fileObject;

	if (inputFile) {
		let fileExtension = inputFile.name.split('.').pop();
		let r = new FileReader();
		r.onload = function (e) {
			let content = e.target.result;
			if (fileExtension == "json") {
				constraints.fixedNodeConstraint = undefined;
				constraints.alignmentConstraint = undefined;
				constraints.relativePlacementConstraint = undefined;        
				let constraintObject = JSON.parse( content );
				if(constraintObject.fixedNodeConstraint)
					constraints.fixedNodeConstraint = constraintObject.fixedNodeConstraint;
				if(constraintObject.alignmentConstraint)
					constraints.alignmentConstraint = constraintObject.alignmentConstraint;
				if(constraintObject.relativePlacementConstraint)
					constraints.relativePlacementConstraint = constraintObject.relativePlacementConstraint;
				clearConstraintListTable();
				fillConstraintListTableFromConstraints();
			}
		};
		r.addEventListener('loadend', function () {});
		r.readAsText(inputFile);
	} else {
		alert("Failed to load file");
	}
	$("#inputFile").val(null);
});

document.getElementById("exportConstraint").addEventListener("click", function(){
	let constraintString = JSON.stringify(constraints, null, 2);
	download('constraint.json', constraintString);
});

let download = function(filename, text) {
		let pom = document.createElement('a');
		pom.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
		pom.setAttribute('download', filename);

		if (document.createEvent) {
				let event = document.createEvent('MouseEvents');
				event.initEvent('click', true, true);
				pom.dispatchEvent(event);
		}
		else {
				pom.click();
		}
};


document.getElementById("sample").addEventListener("change", function(){
	cy.startBatch();
	cy.elements().remove();
	cy.style().clear();
	
	let selectionObject = document.getElementById("sample");
	
	let selected = selectionObject.options[selectionObject.selectedIndex].index;
	if(selected == 0){
		cy.add(elements1);
		applyPostLoadOperations(selected);
	}
	else if(selected == 1){
		cy.add(elements2);
		applyPostLoadOperations(selected);
	}
	else if(selected == 2){
		cy.add(elements3);
		applyPostLoadOperations(selected);
	}
	else if(selected == 3){
		cy.add(elements4);
		applyPostLoadOperations(selected);
	}
	else if(selected == 4){
		cy.add(elements5);
		applyPostLoadOperations(selected);
	}    

	function applyPostLoadOperations(selected){
		cy.nodes().forEach(function(node){
			let size = Math.random()*40+30;
			node.css("width", size);
			node.css("height", size);   
		});
		cy.style(defaultStylesheet);
		
		clearConstraintListTable();
		constraints.fixedNodeConstraint = undefined;
		constraints.alignmentConstraint = undefined;
		constraints.relativePlacementConstraint = undefined;
		
		if(selected == 0){
			if(sample1_constraints.fixedNodeConstraint)
				constraints.fixedNodeConstraint = JSON.parse(JSON.stringify(sample1_constraints.fixedNodeConstraint));
			clearConstraintListTable();
			fillConstraintListTableFromConstraints(); 
		}    
		if(selected == 1){
			if(sample2_constraints.alignmentConstraint)
				constraints.alignmentConstraint = JSON.parse(JSON.stringify(sample2_constraints.alignmentConstraint));
			clearConstraintListTable();
			fillConstraintListTableFromConstraints(); 
		}
		if(selected == 2){
			if(sample3_constraints.relativePlacementConstraint)
				constraints.relativePlacementConstraint = JSON.parse(JSON.stringify(sample3_constraints.relativePlacementConstraint));
			clearConstraintListTable();
			fillConstraintListTableFromConstraints(); 
		}    
		if(selected == 3){
			if(sample4_constraints.fixedNodeConstraint)
				constraints.fixedNodeConstraint = JSON.parse(JSON.stringify(sample4_constraints.fixedNodeConstraint));
			if(sample4_constraints.alignmentConstraint)
				constraints.alignmentConstraint = JSON.parse(JSON.stringify(sample4_constraints.alignmentConstraint));
			if(sample4_constraints.relativePlacementConstraint)
				constraints.relativePlacementConstraint = JSON.parse(JSON.stringify(sample4_constraints.relativePlacementConstraint));
			clearConstraintListTable();
			fillConstraintListTableFromConstraints(); 
		}     
	}
	cy.endBatch();

	if(selected == 4){  
		cy.nodes().not(":parent").positions(function(node, i){
			return {
				x: elements5_positions[i].x,
				y: elements5_positions[i].y
			};    
		});
		cy.layout({name: "preset", fit:true, animate:true, animationDuration: 1000, animationEasing: undefined}).run();
	}
	else {
		let finalOptions = Object.assign({}, options);
		finalOptions.step = "all";
		cy.layout(finalOptions).run();
	}
//  cy.layout({name: 'random', padding: 100}).run();
	onLoad();  

	document.getElementById("nodeList").addEventListener("change", function(){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
});

// Layout buttons

let options = {
	name: 'fcose',
	quality: "proof",
	nodeDimensionsIncludeLabels: true,
	randomize: false,
	animate: true,
	animationDuration: 1000,
	animationEasing: undefined,
	fit: true,
	padding: 30,
	nestingFactor: 0.8,
	nodeSeparation: 250,
	gravityRangeCompound: 1.5,
	gravityCompound: 1.0,
	numIter: 5000,
	// Node repulsion (non overlapping) multiplier
	nodeRepulsion: _node => 15000,
	// Ideal edge (non nested) length
	idealEdgeLength: _edge => 75,
	// Divisor to compute edge forces
	edgeElasticity: _edge => 0.8,
};

// Randomize
document.getElementById("randomizeButton").addEventListener("click", function () {
	let layout = cy.layout({
		name: 'random',
		animate: true
	});

	layout.run();
});

// Fcose
document.getElementById("fcoseButton").addEventListener("click", function(){
	let finalOptions = Object.assign({}, options);
	finalOptions.step = "all";
	finalOptions.randomize = !(document.getElementById("incremental").checked);
	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;
	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
	cy.layoutUtilities("get").setOption("randomize", finalOptions.randomize);
	let start = performance.now();
	layout.run();
	console.log("fCOSE ran in " + (performance.now() - start) + " ms" );
});

// Draft
document.getElementById("draftButton").addEventListener("click", function(){
	let finalOptions = Object.assign({}, options);
	finalOptions.quality = "draft";
	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;  
	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
	cy.layoutUtilities("get").setOption("randomize", true);
	layout.run();
});

// Transform
document.getElementById("transformButton").addEventListener("click", function(){
	let finalOptions = Object.assign({}, options);
	finalOptions.step = "transformed";
	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;
	
	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});            
	layout.run();
});

// Enforce
document.getElementById("enforceButton").addEventListener("click", function(){
	let finalOptions = Object.assign({}, options);
	finalOptions.step = "enforced";
	
	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;

	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});            
	layout.run();
});

document.getElementById("coseButton").addEventListener("click", function(){
	let finalOptions = Object.assign({}, options);
	
	if(document.getElementById("sample").value == "sample6"){
		finalOptions.nestingFactor = 0.4;
		finalOptions.gravityRangeCompound = 0;
		finalOptions.gravityCompound = 3.0;
	}
	
	if(document.getElementById("sample").value == "sample8"){
		finalOptions.idealEdgeLength = 70; 
	}   

	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;
	
	finalOptions.randomize = false;
	finalOptions.step = "cose";  
	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
	cy.layoutUtilities("get").setOption("randomize", finalOptions.randomize);
	layout.run();
});

// Handle Constraints ----------------------------

let onLoad = function(){
	let nodeList = "<select id='nodeList' class='custom-select custom-select-sm' style='width:auto;' onchange='onSelect()'>";
	let simpleNodes = cy.nodes().not(":parent");
	for(let i = 0; i < simpleNodes.length; i++){
		let node = simpleNodes[i];
		let label = (node.data('label'))?(node.data('label')):(node.id());
		if(label.length > 15)
			label = label.substring(0, 12).concat("...");
		nodeList += "<option value='" + cy.nodes().not(":parent")[i].id() + "'>" + label + "</option>";
	}
	let listComponentForFixed = document.getElementById("nodeListColumn");
	listComponentForFixed.innerHTML = nodeList;
	document.getElementById("fixedNodeX").value = Math.round(cy.nodes().not(":parent")[0].position("x"));
	document.getElementById("fixedNodeY").value = Math.round(cy.nodes().not(":parent")[0].position("y"));

	let nodeListRP1 = "<select id='nodeListRP1' class='custom-select custom-select-sm' style='width:auto;' onchange='onSelectRP1()'>";
	for(let i = 0; i < simpleNodes.length; i++){
		let node = simpleNodes[i];
		let label = (node.data('label'))?(node.data('label')):(node.id()); 
		if(label.length > 15)
			label = label.substring(0, 12).concat("...");    
		nodeListRP1 += "<option value=" + cy.nodes().not(":parent")[i].id() + ">" + label + "</option>";
	}

	let nodeListRP2 = "<select id='nodeListRP2' class='custom-select custom-select-sm' style='width:auto;' onchange='onSelectRP2()'>";
	for(let i = 0; i < simpleNodes.length; i++){
		let node = simpleNodes[i];
		let label = (node.data('label'))?(node.data('label')):(node.id());
		if(label.length > 15)
			label = label.substring(0, 12).concat("...");    
		nodeListRP2 += "<option value=" + cy.nodes().not(":parent")[i].id() + ">" + label + "</option>";
	}            

	let listComponentForRP1 = document.getElementById("nodeListColumnRP1");
	listComponentForRP1.innerHTML = nodeListRP1;

	let listComponentForRP2 = document.getElementById("nodeListColumnRP2");
	listComponentForRP2.innerHTML = nodeListRP2;            
};

let onSelect = function(){
	let id = document.getElementById("nodeList").value;
	cy.elements().unselect();
	cy.getElementById(id).select();
};

let onSelectRP1 = function(){
	let id = document.getElementById("nodeListRP1").value;
	cy.elements().unselect();
	cy.getElementById(id).select();
};

let onSelectRP2 = function(){
	let id = document.getElementById("nodeListRP2").value;
	cy.elements().unselect();
	cy.getElementById(id).select();
};

document.addEventListener('DOMContentLoaded', function(){
	document.getElementById("nodeList").addEventListener("change", function(){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
});

cy.ready( function(event){
	onLoad();
});

document.getElementById("nodeList").addEventListener("change", function(){
	document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
	document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
});

cy.on("position", "node", function(event) {
	if(event.target.id() == document.getElementById("nodeList").value){
		document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	}
});


document.getElementById("fixedNode").addEventListener("click",function(){
	let nodeId = document.getElementById("nodeList").value;
	let exist = false;
	if(constraints.fixedNodeConstraint){
		constraints.fixedNodeConstraint.forEach(function(constraintObject){
			if(constraintObject.nodeId == nodeId){
				exist = true;
			}
		}); 
	}
	if(!exist){
		let fixedNode = {nodeId: nodeId, position: Object.assign({}, {x: parseInt(document.getElementById("fixedNodeX").value), y: parseInt(document.getElementById("fixedNodeY").value)})};
		if(constraints.fixedNodeConstraint){
			constraints.fixedNodeConstraint.push(fixedNode);
		}
		else{
			constraints.fixedNodeConstraint = [fixedNode];
		}
			
		addToHistory("Fixed", [nodeId], fixedNode.position);
	}
});

document.getElementById("verticalAlignment").addEventListener("click", function(){
	if(cy.nodes(":selected").not(":parent").length > 0){
		let valignArray = [];
		cy.nodes(":selected").not(":parent").forEach(function(node){
			valignArray.push(node.id());
		});
		if(constraints.alignmentConstraint){
			if(constraints.alignmentConstraint.vertical){
				constraints.alignmentConstraint.vertical.push(valignArray);
			}
			else{
				constraints.alignmentConstraint.vertical = [valignArray];
			}
		}
		else{
			constraints.alignmentConstraint = {};
			constraints.alignmentConstraint.vertical = [valignArray];
		}
		addToHistory("Alignment", valignArray, 'vertical'); 
	}
});

document.getElementById("horizontalAlignment").addEventListener("click", function(){
	if(cy.nodes(":selected").not(":parent").length > 0){
		let halignArray = [];
		cy.nodes(":selected").not(":parent").forEach(function(node){
			halignArray.push(node.id());
		});
		if(constraints.alignmentConstraint){
			if(constraints.alignmentConstraint.horizontal){
				constraints.alignmentConstraint.horizontal.push(halignArray);
			}
			else{
				constraints.alignmentConstraint.horizontal = [halignArray];
			}
		}
		else{
			constraints.alignmentConstraint = {};
			constraints.alignmentConstraint.horizontal = [halignArray];
		}
		addToHistory("Alignment", halignArray, 'horizontal'); 
	}
});

document.getElementById("relativePlacement").addEventListener("click", function(){
	let nodeId1 = document.getElementById("nodeListRP1").value;
	let nodeId2 = document.getElementById("nodeListRP2").value;
	let isExist = false;
	if(constraints.relativePlacementConstraint){
		constraints.relativePlacementConstraint.forEach(function(constraint){
			if(constraint["left"]){
				if((constraint["left"] == nodeId1 && constraint["right"] == nodeId2 || constraint["left"] == nodeId2 && constraint["right"] == nodeId1) && document.getElementById("directionList").value == "left-right"){
					isExist = true;
				}
			}
			else {
				if((constraint["top"] == nodeId1 && constraint["bottom"] == nodeId2 || constraint["top"] == nodeId2 && constraint["bottom"] == nodeId1) && document.getElementById("directionList").value == "top-bottom"){
					isExist = true;
				}
			}
		});
	}
	if((nodeId1 != nodeId2) && !isExist){
		let relativePlacementConstraint;
		if(document.getElementById("directionList").value == "left-right"){
			relativePlacementConstraint = {left: nodeId1, right: nodeId2, gap: (document.getElementById("gap").value) ? (parseInt(document.getElementById("gap").value)) : undefined};
		}
		else{
			relativePlacementConstraint = {top: nodeId1, bottom: nodeId2, gap: (document.getElementById("gap").value) ? (parseInt(document.getElementById("gap").value)) : undefined};
		}            
		if(constraints.relativePlacementConstraint){
			constraints.relativePlacementConstraint.push(relativePlacementConstraint);
		}
		else{
			constraints.relativePlacementConstraint = [];
			constraints.relativePlacementConstraint.push(relativePlacementConstraint);
		}
		
		if(document.getElementById("directionList").value == "left-right")
			addToHistory("Relative", [nodeId1, nodeId2], 'l-r - ' + ((document.getElementById("gap").value) ? (parseInt(document.getElementById("gap").value)) : parseInt(cy.getElementById(nodeId1).width()/2 + cy.getElementById(nodeId2).width()/2 + 50)));
		else{
			addToHistory("Relative", [nodeId1, nodeId2], 't-b - ' + ((document.getElementById("gap").value) ? (parseInt(document.getElementById("gap").value)) : parseInt(cy.getElementById(nodeId1).height()/2 + cy.getElementById(nodeId2).height()/2 + 50)));
		}
	}
});



// Delete Row Elements
let deleteRowElements = function (row, nodeIds, info) {
	let constraintType = row.cells[0].innerHTML;
	if (constraintType == 'Fixed') {
		constraints.fixedNodeConstraint.forEach(function (item, index) {
			if (item.nodeId == nodeIds[0]) {
				constraints.fixedNodeConstraint.splice(index, 1);
			}
		});
		if (constraints.fixedNodeConstraint.length == 0) {
			constraints.fixedNodeConstraint = undefined;
		}
	} else if (constraintType == 'Alignment') {
		if (info == 'vertical') {
			constraints.alignmentConstraint.vertical.forEach(function (item, index) {
				if (item.length == nodeIds.length) {
					let equal = true;
					item.forEach(function (nodeId, i) {
						if (nodeId != nodeIds[i]) {
							equal = false;
						}
					});
					if (equal) {
						constraints.alignmentConstraint.vertical.splice(index, 1);
						if (constraints.alignmentConstraint.vertical.length == 0) {
							delete constraints.alignmentConstraint.vertical;
							if (!constraints.alignmentConstraint.horizontal) {
								constraints.alignmentConstraint = undefined;
							}
						}
					}
				}
			});
		} else {
			constraints.alignmentConstraint.horizontal.forEach(function (item, index) {
				if (item.length == nodeIds.length) {
					let equal = true;
					item.forEach(function (nodeId, i) {
						if (nodeId != nodeIds[i]) {
							equal = false;
						}
					});
					if (equal) {
						constraints.alignmentConstraint.horizontal.splice(index, 1);
						if (constraints.alignmentConstraint.horizontal.length == 0) {
							delete constraints.alignmentConstraint.horizontal;
							if (!constraints.alignmentConstraint.vertical) {
								constraints.alignmentConstraint = undefined;
							}
						}
					}
				}
			});
		}
	}
	else{
		constraints.relativePlacementConstraint.forEach(function(item, index){
			if(info.substring(0,1) == 'l'){
				if(item.left && item.left == nodeIds[0] && item.right == nodeIds[1]){
					constraints.relativePlacementConstraint.splice(index, 1);
					if(constraints.relativePlacementConstraint.length == 0){
						constraints.relativePlacementConstraint = undefined;
					}
				}
			}
			else{
				if(item.top && item.top == nodeIds[0] && item.bottom == nodeIds[1]){
					constraints.relativePlacementConstraint.splice(index, 1);
					if(constraints.relativePlacementConstraint.length == 0){
						constraints.relativePlacementConstraint = undefined;
					}
				}
			}
		});
	}
	constraintListTable.deleteRow(row.rowIndex);
};