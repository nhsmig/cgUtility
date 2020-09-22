#-*- coding: utf-8 -*-
import maya.cmds as cmds
import os
import sys
import pprint as pp

#마야 머티리얼에 연결된 텍스쳐의 연관텍스쳐(노말,스페큘러,에미션)가 있는지 확인하여 기본 텍스쳐노드와 연관 텍스쳐파일 목록을 반환
def doFindTextures(mayaMat):
	fileNode = []
	textureList = {'fileNode':'', 'path':'', 'type':'', 'diffuse':'', 'normal':'', 'specular':'', 'specularAlt':'', 'emission':''}
	try:
		fileNode = cmds.listConnections(mayaMat, type = 'file')[0]
	except:
		fileNode = False
	if fileNode:
		textureFile = cmds.getAttr(fileNode + '.fileTextureName')
		if textureFile:
			textureList['fileNode'] = fileNode
			textureList['diffuse'] = textureFile.split('/')[-1:][0]
			# print textureList['diffuse']
			fileType = textureList['diffuse'].split('.')[0].split('_')[-1]
			# print fileType
			textureList['type'] = fileType
			textureList['path'] = textureFile.rstrip(textureList['diffuse'])
			textureList['normal'] = textureList['diffuse'].replace(fileType, 'NORMAL')
			textureList['specular'] = textureList['diffuse'].replace(fileType, 'SRMA')
			textureList['specularAlt'] = textureList['diffuse'].replace(fileType, 'SPEC')
			textureList['emission'] = textureList['diffuse'].replace(fileType, 'EM')
			
			for k,v in textureList.items():
				if k is not 'fileNode' and k is not 'path':
					if k is not 'type':
						fullPath = textureList['path'] + v
						if os.path.isfile(fullPath):
							textureList[k] = v	
						else:
							textureList[k] = ''
	else:
		textureList['fileNode'] = ''
	return textureList
	
#텍스쳐 컬러스페이스 옵션 고정	
def setColorspace(fileNode, colorSpace):
	cmds.setAttr(fileNode + '.colorSpace', colorSpace, type = 'string')
	cmds.setAttr(fileNode + '.ignoreColorSpaceFileRules', lock = False)
	cmds.setAttr(fileNode + '.ignoreColorSpaceFileRules', 1)
	cmds.setAttr(fileNode + '.ignoreColorSpaceFileRules', lock = True)

#bump2d 노드 설정
def setAiNormal(bumpNode):
	aiBumpOptions = {'.aiFlipR':'0', '.aiFlipG':'0', '.aiSwapTangents':'0', '.aiUseDerivatives':'1', '.bumpInterp':'1'}
	for k,v in aiBumpOptions.items():
		cmds.setAttr(bumpNode + k, int(v))
		
#file 노드와 place2dTexture 노드를 연결
def connTexPlacement(source, target):
	socket = { 
	'.offsetU':'.offsetU', '.offsetV':'.offsetV', '.outUV':'.uvCoord', '.outUvFilterSize':'.uvFilterSize', 
	'.repeatU':'.repeatU', '.repeatV':'.repeatV', '.rotateFrame':'.rotateFrame', '.vertexCameraOne':'.vertexCameraOne', 
	'.vertexUvOne':'.vertexUvOne', '.vertexUvTwo':'.vertexUvTwo', '.vertexUvThree':'.vertexUvThree' 
	}
	
	for k,v in socket.items():
		cmds.connectAttr((source + k), (target + v))
	
		
#셰이딩그룹에 연결된 마야 기본 머티리얼과 같은 이름의 아놀드 머티리얼을 생성하고 텍스쳐를 연결.
#텍스쳐 폴더에 스페큘러나 노말맵등의 연관 파일이 있는 경우 불러들여 적절한 채널에 연결
#마야 머티리얼에 이미 해당 채널 연결이 있는 경우 새로 불러들이지 않고 기존 연결을 사용함

def main():
	sel = cmds.ls(selection = True, type = 'shadingEngine')

	if not sel:
		print('no shading group selected')
		sel = cmds.ls(type = 'shadingEngine')
		remove = ['initialShadingGroup', 'initialParticleSE']
		sel = list(set(sel) - set(remove))

	for eachSG in sel:
		mayaMat = cmds.ls(cmds.listConnections(eachSG),materials = True)
		
		#셰이딩그룹의 .surfaceshader에 연결된 머티리얼이 있다면 같은 이름의 아놀드 셰이더를 생성하여 텍스쳐를 연결
		for eachMat in mayaMat:
			plugSG = cmds.listConnections(eachMat, source = False, destination = True, plugs = True, type = 'shadingEngine')
			
			if '.surfaceShader' in plugSG[0]:			
				if not cmds.connectionInfo(eachSG + '.aiSurfaceShader', isDestination = True):
					textureList = doFindTextures(eachMat)
					aiMat = cmds.shadingNode('aiStandardSurface', asShader = True, name = 'ai_' + eachMat)
					cmds.setAttr(aiMat + '.base', 1)
					cmds.connectAttr(aiMat + '.outColor', eachSG + '.aiSurfaceShader')
					
					print('textureList = \n')
					print textureList

					if textureList['fileNode']:
						texturePlaceNode = ''
						try:
							texturePlaceNode = cmds.listConnections(textureList['fileNode'], type = 'place2dTexture')[0]
						except:
							texturePlaceNode = cmds.shadingNode('place2dTexture', asUtility = True, name = 'place2dTexture')
							connTexPlacement(texturePlaceNode, textureList['fileNode'])
						
						fileType = textureList['type']
						print('fileType = ' + fileType)

						for k,v in textureList.items():
							#디퓨즈맵 연결
							if k is 'diffuse' and v is not '':
								cmds.connectAttr(textureList['fileNode'] + '.outColor', aiMat + '.baseColor') 
							#노말맵 연결
							elif k is 'normal' and v is not '':
								bumpInput = cmds.connectionInfo(eachMat + '.normalCamera', sourceFromDestination = True)
								if bumpInput:
									bumpNode = bumpInput.split('.')[0]
									setAiNormal(bumpNode)
									cmds.connectAttr(bumpInput, aiMat + '.normalCamera')
									bumpTextureInput = cmds.connectionInfo(bumpNode + '.bumpValue', sourceFromDestination = True)
									if bumpTextureInput:
										bumpFileNode = bumpTextureInput.split('.')[0]
										bumpPlacementNode = cmds.listConnections(bumpFileNode, source = True, destination = False, type = 'place2dTexture')
										setColorspace(bumpFileNode, 'Raw')
										if not bumpPlacementNode:
											connTexPlacement(texturePlaceNode, bumpFileNode)
										else:
											continue
									else:
										bumpFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['normal'].split('.')[0])
										cmds.setAttr(bumpFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
										setColorspace(bumpFileNode, 'Raw')
										setAiNormal(bumpNode)
										connTexPlacement(texturePlaceNode, bumpFileNode)			
										cmds.connectAttr(bumpFileNode + '.outAlpha', bumpNode + '.bumpValue')
								else:
									bumpFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['normal'].split('.')[0])
									cmds.setAttr(bumpFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
									setColorspace(bumpFileNode, 'Raw')
									bumpNode = cmds.shadingNode('bump2d', asUtility = True, name = textureList['normal'].split('.')[0] + '_bump2d')
									setAiNormal(bumpNode)
									connTexPlacement(texturePlaceNode, bumpFileNode)			
									cmds.connectAttr(bumpFileNode + '.outAlpha', bumpNode + '.bumpValue')
									cmds.connectAttr(bumpNode + '.outNormal', aiMat + '.normalCamera')
								
									
							#스페큘러맵이 있다면 연결(SRMA규칙에 따름) 없다면 roughness를 0.8로 설정 
							elif k is 'specular' and v:
								specFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['specular'].split('.')[0])
								cmds.setAttr(specFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
								setColorspace(specFileNode, 'Raw')
								connTexPlacement(texturePlaceNode, specFileNode)
								cmds.connectAttr(specFileNode + '.outColorR', aiMat + '.specular')
								cmds.connectAttr(specFileNode + '.outColorG', aiMat + '.specularRoughness')
								cmds.connectAttr(specFileNode + '.outColorB', aiMat + '.metalness')
							
							elif k is 'specularAlt' and v:
								# print k
								# print v
								if fileType == 'BM':
									specFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['specularAlt'].split('.')[0])
									cmds.setAttr(specFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
									setColorspace(specFileNode, 'Raw')
									connTexPlacement(texturePlaceNode, specFileNode)
									cmds.connectAttr(specFileNode + '.outColorR', aiMat + '.specular')
									cmds.connectAttr(specFileNode + '.outColorG', aiMat + '.specularRoughness')
									cmds.connectAttr(specFileNode + '.outColorB', aiMat + '.metalness')		

								else:
									specFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['specularAlt'].split('.')[0])
									cmds.setAttr(specFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
									setColorspace(specFileNode, 'Raw')
									connTexPlacement(texturePlaceNode, specFileNode)
									cmds.connectAttr(specFileNode + '.outColorR', aiMat + '.specular')
									cmds.setAttr(aiMat + '.specularRoughness', 0.5)
									# cmds.connectAttr(specFileNode + '.outColorG', aiMat + '.specularRoughness')
									# cmds.connectAttr(specFileNode + '.outColorB', aiMat + '.metalness')

							elif (k is 'specularAlt' and not v) and (k is 'specular' and not v):
								cmds.setAttr(aiMat + '.specularRoughness', 0.8)

							#에미션 맵이 있다면 AOV/id1에 연결하고 값을 glow로 설정, weight 1로 설정,  diffuse color를 emissionColor에 연결
							elif k is 'emission' and v is not '':
								emissionFileNode = cmds.shadingNode('file', asTexture = True, isColorManaged = True, name = textureList['emission'].split('.')[0])
								cmds.setAttr(emissionFileNode + '.fileTextureName', textureList['path'] + v, type = 'string')
								cmds.setAttr(emissionFileNode + '.alphaIsLuminance', 1)
								setColorspace(emissionFileNode, 'Raw')
								connTexPlacement(texturePlaceNode, emissionFileNode)
								cmds.connectAttr(emissionFileNode + '.outColor', aiMat + '.id1')
								cmds.connectAttr(emissionFileNode + '.outAlpha', aiMat + '.emission')
								cmds.setAttr(aiMat + '.aovId1', 'glow', type = 'string')
								cmds.connectAttr(textureList['fileNode'] + '.outColor', aiMat + '.emissionColor')
							else:
								continue
					else:
						continue									  
			else:
				continue
if __name__ == '__main__':
    main()
				
				
			
