#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet@gmail.com
#


# ssh -i .ssh/aws.pem ec2-user@ec2-184-72-164-79.compute-1.amazonaws.com

import logging,sys,time
from boto.ec2.connection import EC2Connection


log=logging.getLogger('main')

class FreeInstance():
  ''' Access to EC@ free instance.
  
      t1.micro, and etc.. cinditions on the First year.
  '''
  connection=None
  instance=None
  def __init__(self):
    self.log=logging.getLogger(self.__class__.__name__)
    #envars
    #AWS_ACCESS_KEY_ID - Your AWS Access Key ID AWS_SECRET_ACCESS_KEY - Your AWS Secret Access Key
    #conn = EC2Connection('<aws access key>', '<aws secret key>')
    self.connection = EC2Connection()

  def get_not_terminated(self):
    reservations = self.connection.get_all_instances()
    notTerminated=[instance for reservation in reservations for instance in reservation.instances if instance.state != 'terminated']
    if len(notTerminated) > 0:
      if len(notTerminated) > 1:
        self.log.error('Too much instances ! : %d not terminated'%( len(notTerminated)) )
      self.instance=notTerminated[0]
      return notTerminated
    else:
      self.instance=None
    # else all
    return []
    
  def has_existing(self):
    running = False
    for instance in self.get_not_terminated():
      if instance.state == 'running':
        self.log.error(' %s : %s'%(instance.public_dns_name,instance.state))
      else:
        self.log.error(' %s : %s'%(instance.id,instance.state))
      running=True
    return running

  def wait_for_running(self):  
    pending=False
    time.sleep(1.0)
    for wait in range(1,100):
      pending=False
      for instance in self.get_not_terminated():
        instance.update()
        if instance.state == 'pending':
          time.sleep(wait)
          self.log.info('instance is in state %s'%(instance.state))
          pending=True
      if not pending:
        break
    
  def print_running(self):
    for instance in self.get_not_terminated():
      if instance.state == 'running':
        self.log.info('%s: %s : "%s"'%(instance.public_dns_name,instance.state,'ssh -i ~/.ssh/aws.pem ubuntu@'+instance.public_dns_name))
    return

  def launch_free(self):
    # lenny 32 bit : 'ami-dcf615b5' - instance store
    # ubuntu 10.10 32 bits, EBS store : 'ami-ccf405a5'
    image_ids=['ami-ccf405a5']
    images= self.connection.get_all_images(image_ids=image_ids)
    #run images[0]
    image=images[0]
    # default is small instance & cie
    # free is t1.micro
    instance_type='t1.micro'
    security_groups=['SSH','DNS']
    #running
    reservation = image.run(1,1,'aws',security_groups,instance_type=instance_type)
    return reservation

    
  def want_to_stop_free_instance(self):
    userSays=raw_input('Do you want to kill the active instance (y/n) ? ')
    if userSays == 'y':
      self.kill_all_instances()
      return True
    elif userSays == 'n':
      return False
    else:
      return False

  def kill_all_instances(self):
    instances=self.get_not_terminated()
    for instance in instances:  
      instance.stop()
    self.log.debug(instances)
    shutting=False
    for wait in range(1,100):
      shutting=False
      for instance in instances:
        instance.update()
        if instance.state != 'terminated':
          time.sleep(wait)
          self.log.info('instance %s is %s'%(instance,instance.state))
          shutting=True
      if not shutting:
        break
    return

  def start(self):  
    if self.has_existing():
      self.log.info('Aborting launch..')
      self.print_running()
      if(self.want_to_stop_free_instance()):
        self.kill_all_instances()
        return None
      else :
        return self.get_instance()      
    else:
      self.log.info('Launching Free Instance')
      self.instance=self.launch_free()
      self.wait_for_running()
      self.print_running()
      return self.get_instance()

  def run(self):
    instance=self.start()
    if instance is None:
      ret=raw_input('Do you want to restart ?')
      if ret == 'y':
        instance=self.start()        
    return instance

  def get_instance(self):
    return self.instance

def main(argv):
  logging.basicConfig(level=logging.INFO)
  logging.getLogger('main').setLevel(logging.DEBUG)

  free=FreeInstance()
  i=free.run()
  if not i is None:
    logging.info('Launching system update...')
    from sysadmin import AdminInstance
    admin=AdminInstance(free.get_instance(),username='ubuntu')
    admin.update() 
    free.print_running()
    
  sys.exit()

main(sys.argv)


