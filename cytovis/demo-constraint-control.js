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

let constraints = {
	fixedNodeConstraint: undefined,
	alignmentConstraint: undefined,
	relativePlacementConstraint: undefined
};

// Setup cytoscape inside the cy container using the stylesheet from above.

let cy = window.cy = cytoscape({
	container: document.getElementById('cy'),
	ready: function(){              
		let initialLayout = this.layout({
			name: 'fcose',
			step: 'all',
			animationEasing: 'ease-out'
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

// Handle file constraints input element.
document.getElementById("openConstraintFile").addEventListener("click", function () {
	document.getElementById("inputConstraint").click();
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
				let constraintObject = JSON.parse(content);
				if(constraintObject.fixedNodeConstraint)
					constraints.fixedNodeConstraint = constraintObject.fixedNodeConstraint;
				if(constraintObject.alignmentConstraint)
					constraints.alignmentConstraint = constraintObject.alignmentConstraint;
				if(constraintObject.relativePlacementConstraint)
					constraints.relativePlacementConstraint = constraintObject.relativePlacementConstraint;
			}
		};
		r.addEventListener('loadend', function () {});
		r.addEventListener('loadend', function () {
			 // do stuff here when r is done loading if needed.
		});
		r.readAsText(inputFile);
	} else {
		alert("Failed to load file");
	}
	$("#inputFile").val(null);
});

// Handle file input element.
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
			 // do stuff here when r is done loading if needed.
		});
		r.readAsText(inputFile);
	} else {
		alert("Failed to load file");
	}
	$("#inputFile").val(null);
});

// Auto align graph
document.getElementById("fcoseButton").addEventListener("click", function(){
	let finalOptions = {}; //Object.assign({}, options);
	finalOptions.name = "fcose";
	finalOptions.step = "all";
	finalOptions.randomize = false;
	finalOptions.fixedNodeConstraint = constraints.fixedNodeConstraint ? constraints.fixedNodeConstraint : undefined;
	finalOptions.alignmentConstraint = constraints.alignmentConstraint ? constraints.alignmentConstraint : undefined;
	finalOptions.relativePlacementConstraint = constraints.relativePlacementConstraint ? constraints.relativePlacementConstraint : undefined;

	let layout = cy.layout(finalOptions);
	layout.one("layoutstop", function( event ){
		//document.getElementById("fixedNodeX").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("x"));
		//document.getElementById("fixedNodeY").value = Math.round(cy.getElementById(document.getElementById("nodeList").value).position("y"));
	});
	cy.layoutUtilities("get").setOption("randomize", finalOptions.randomize);
	let start = performance.now();
	layout.run();
	console.log("fCOSE ran in " + (performance.now() - start) + " ms" );
});

cy.ready( function(event){
	// do stuff here if you want
});