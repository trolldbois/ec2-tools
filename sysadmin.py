#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet@gmail.com
#

import logging
import paramiko,os,sys

sys.path.append('/usr/sbin/')
import ipcheck

def checkRunning(instance):
  assert not instance is None
  assert instance.state == 'running'


class AdminInstance():
  '''
    Update the AMI image through ssh to be up to date.
  '''
  instance=None
  ssh=None
  __updateCommands=['uname -a','sudo apt-get update -y','sudo apt-get dist-upgrade -y','df -h']
  DNSTUNNEL_DOMAIN='ipdns.rbns.org'
  DNSTUNNEL_PASSWORD='JAGDLHD848wtdgkq79wtqidgKG'
  dyndns="aLPCOABSDvjYb1EH5k9h1IaXuFPd3WSbxKo"
  def __init__(self,instance,username='ec2-user',keypair='~/.ssh/aws.pem'):
    checkRunning(instance)
    self.instance=instance
    self.host=instance.ip_address
    self.port=22
    self.privatekeyfile = os.path.expanduser(keypair)
    self.username=username
    self.log=logging.getLogger(self.__class__.__name__)
  
  def _connect(self):
    if self.ssh is not None and self.ssh.get_transport() is not None:
      return
    mykey = paramiko.RSAKey.from_private_key_file(self.privatekeyfile)
    self.ssh= paramiko.SSHClient()
    self.ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
    self.ssh.connect(self.host,username=self.username,pkey = mykey)
  
  def _execute(self,cmd):
    self.log.info(cmd)
    stdin, stdout, stderr = self.ssh.exec_command(cmd)
    self.log.info(stdout.readlines())
    self.log.warning(stderr.readlines())
  
  def update(self):
    self._connect()
    self.updateSystemPackages()
    self.installSoftware()
    self.updateDyndns()
    self.configureTunnels()
  
  def updateSystemPackages(self):
    #update package
    for cmd in self.__updateCommands:
      self._execute(cmd)
    #ssh.close()

  def installSoftware(self):  
    installCommands=['sudo apt-get install iodine ipcheck',
    'sudo iodined -P %s %s %s'%(self.DNSTUNNEL_PASSWORD,self.instance.ip_address,self.DNSTUNNEL_DOMAIN)]
    for cmd in installCommands:
      self._execute(cmd)    

  def updateDyndns(self):
    #ipcheck._main(['ipcheck','--makedat','-a',self.instance.ip_address, 'rbns',self.dyndns,'rbns.dyndns.info'])
    commands=['rm ipcheck.dat',
    'ipcheck --makedat -a %s %s %s %s'%(self.instance.ip_address, 'rbns',self.dyndns,'rbns.dyndns.info') ]
    for cmd in commands:
      self._execute(cmd)    
    pass  
        
  def configureTunnels(self):
    commands=[
    'sudo iodined -P %s %s %s'%(self.DNSTUNNEL_PASSWORD,self.instance.ip_address,self.DNSTUNNEL_DOMAIN)]
    for cmd in commands:
      self._execute(cmd)    
    




   
 
