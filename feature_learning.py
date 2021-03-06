# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 17:26:38 2019

@author: user
"""

from sklearn.model_selection import KFold
#from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
import os

import train_data_raw_pa_hapt_100 as tr
import test_data_raw_pa_hapt_100 as ts


fold = 1
use_bias = 1

is_get_data = 0 # get train data and test data
is_add_noise = 0
is_create_batches = 0
is_train = 0
is_load = 0 # reload model
is_analyse = 1
is_get_weights = 0

if is_get_data:
    train_data, train_label = tr.get_train_data(fold)
    test_data, test_label = ts.get_test_data(fold)
smpl, n_length, n_channels = train_data.shape[0],train_data.shape[1],train_data.shape[2]

noise_thres = 0.05
if is_add_noise:
    x_train_noise = np.zeros(shape=(smpl, n_length, n_channels))
    for c in range(0,3):
        noise = np.random.uniform(low=-noise_thres, high=noise_thres, size=(smpl, n_length))
        x_train_noise[:,:,c] = x_train[:,:,c] + noise

if is_create_batches:
    n_batch = 80
    n_smpl = 16
    data_noise = []
    data = []
    tmp = np.where(train_label==0)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==1)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==2)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==3)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==4)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==5)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==6)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    tmp = np.where(train_label==7)[0]
    data_noise.append(x_train_noise[tmp])
    data.append(x_train[tmp])
    
    x_batches = []
    x_noise_batches = []
    batch_y = np.zeros((8*n_smpl,))
    for b in range(n_batch):
        batch = np.empty([0, n_length, n_channels])
        batch_noise = np.empty([0, n_length, n_channels])
        for c in range(0,8):
            tmp = np.random.randint(0,len(data[c]),n_smpl)
            dat = data[c][tmp]
            batch = np.vstack((batch, dat))
            dat = data_noise[c][tmp]
            batch_noise = np.vstack((batch_noise, dat))
        x_batches.append(batch)
        x_noise_batches.append(batch_noise)
        
    st = 0
    ed = n_smpl
    for c in range(0,8):
        batch_y[st:ed] = c
        st = ed; ed = ed+n_smpl
    batch_y = tf.keras.utils.to_categorical(batch_y)
    del batch, batch_noise, tmp, dat, data, data_noise, n_batch, n_smpl, st, ed


epoch = 1000
display_step = 20
min_delta = 0.000001 # elu 0.00001
patience = 100
min_loss_th = 0.001
latent_filter = 4

xavier = tf.contrib.layers.xavier_initializer()
act_fn = tf.nn.elu

dir_model = 'Models/cdae_elu_filters_' + str(latent_filter) + '_fold_' + str(fold) + '/'   # cnn2:maxpool cnn3:avgpool

tf.reset_default_graph()
X_noise = tf.placeholder(tf.float32, shape=(None, n_length, n_channels), name='X_noise')
X = tf.placeholder(tf.float32, shape=(None, n_length, n_channels), name='X')

with tf.name_scope('network'):
    def encoder(inputs, reuse=None):
        with tf.variable_scope('encoder', reuse=reuse):
            conv1 = tf.layers.conv1d(inputs, filters=10,
                                  kernel_size=11, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv1')
            conv1 = tf.layers.dropout(conv1)
            pool1 = tf.layers.max_pooling1d(conv1, 2, 2)
            
            conv2 = tf.layers.conv1d(pool1, filters=20,
                                  kernel_size=9, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv2')
            conv2 = tf.layers.dropout(conv2)
            pool2 = tf.layers.max_pooling1d(conv2, 2, 2)

            conv3 = tf.layers.conv1d(pool2, filters=30,
                                  kernel_size=7, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv3')
            conv3 = tf.layers.dropout(conv3)
            pool3 = tf.layers.max_pooling1d(conv3, 2, 2)
            
            conv4 = tf.layers.conv1d(pool3, filters=40,
                                  kernel_size=5, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv4')
            conv4 = tf.layers.dropout(conv4)
            pool4 = tf.layers.max_pooling1d(conv4, 2, 2)
            
            latent = tf.layers.conv1d(pool4, filters=latent_filter,
                                  kernel_size=3, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='latent')
            
            print('inputs:', inputs.shape)
            print('cv1:',conv1.shape)
            print('p1:', pool1.shape)
            print('cv2:',conv2.shape)
            print('p2:', pool2.shape)
            print('cv3:',conv3.shape)
            print('p3:', pool3.shape)
            print('cv4:',conv4.shape)
            print('p4:', pool4.shape)
            print('latent:',latent.shape)
            
            return latent
    
    def decoder(h, reuse=None):
        with tf.variable_scope('decoder', reuse=reuse):
            conv1 = tf.layers.conv1d(h, filters=40,
                                  kernel_size=3, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv1')
            conv1 = tf.layers.dropout(conv1)
            up1 = tf.keras.layers.UpSampling1D(2)(conv1)
            
            
            conv2 = tf.layers.conv1d(up1, filters=30,   # 6
                                  kernel_size=5, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv2')
            conv2 = tf.layers.dropout(conv2)
            up2 = tf.keras.layers.UpSampling1D(2)(conv2)
            
            conv3 = tf.layers.conv1d(up2, filters=20, # 12
                                  kernel_size=7, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv3')
            conv3 = tf.layers.dropout(conv3)
            conv3 = tf.pad(conv3, tf.constant([[0,0], [0,1], [0,0]]))
            up3 = tf.keras.layers.UpSampling1D(2)(conv3)
            
            conv4 = tf.layers.conv1d(up3, filters=10,   # 24
                                  kernel_size=9, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv4')
            conv4 = tf.layers.dropout(conv4)
            up4 = tf.keras.layers.UpSampling1D(2)(conv4)
            
            logits = tf.layers.conv1d(up4, filters=3,   # 100
                                  kernel_size=11, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='logits')

            print('cv1:',conv1.shape)
            print('up1:',up1.shape)
            print('cv2:',conv2.shape)
            print('up2:',up2.shape)
            print('cv3:',conv3.shape)
            print('up3:',up3.shape)
            print('cv4:',conv4.shape)
            print('up4:',up4.shape)
            print('logits:',logits.shape)
            
            return logits
        
    def discriminator(X, reuse=None):
        with tf.variable_scope('discriminator', reuse=reuse):
            conv1 = tf.layers.conv1d(X, filters=10,
                                  kernel_size=7, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv1')
            conv1 = tf.layers.dropout(conv1)
            pool1 = tf.layers.max_pooling1d(conv1, 2, 2)
            
            conv2 = tf.layers.conv1d(pool1, filters=20,
                                  kernel_size=5, padding='SAME',
                                  strides=1, use_bias=True,
                                  kernel_initializer=xavier,
                                  data_format='channels_last', activation=act_fn, name='conv2')
            conv2 = tf.layers.dropout(conv2)
            pool2 = tf.layers.max_pooling1d(conv2, 2, 2)
            
            pool2_flat = tf.layers.flatten(pool2)
            
            h1 = tf.layers.dense(pool2_flat, 100, activation=act_fn, 
                                 kernel_initializer=xavier,
                                 use_bias=True, bias_initializer=tf.zeros_initializer())
            
            h2 = tf.layers.dense(h1, 50, activation=act_fn, 
                                 kernel_initializer=xavier,
                                 use_bias=True, bias_initializer=tf.zeros_initializer())
            
            disc_logits = tf.layers.dense(h2, 2, activation=None,
                          kernel_initializer=tf.contrib.layers.xavier_initializer(),
                          use_bias=True, bias_initializer=tf.zeros_initializer())
            disc_softmax = tf.nn.softmax(disc_logits)
            print('discriminator')
            print('cv1:',conv1.shape)
            print('p1:', pool1.shape)
            print('cv2:',conv2.shape)
            print('p2:', pool2.shape)
            print('h1:', h1.shape)
            print('h2:', h2.shape)
            print('logits:', disc_logits.shape)
            return disc_softmax
    
    #conv_ae_graph = tf.Graph()
    #with conv_ae_graph.as_default():
    h = encoder(X_noise, reuse=None)
    logits = decoder(h, reuse=None)
    d_logits_real = discriminator(X, reuse=None)
    d_logits_fake = discriminator(logits, reuse=True)

with tf.name_scope('weights'):
    train_weights = tf.trainable_variables() # return all weights
    enc_weights = [w for w in train_weights if 'encoder' in w.name]
    dec_weights = [w for w in train_weights if 'decoder' in w.name]
    disc_weights = [w for w in train_weights if 'discriminator' in w.name]
    
with tf.name_scope('loss'):
    l2_loss = reg_scale * tf.add_n([tf.nn.l2_loss(w) for w in train_weights if 'bias' not in w.name])
    network_loss = np.abs(X - logits)
    
    d_loss_real = tf.reduce_mean(
            tf.nn.sigmoid_cross_entropy_with_logits(labels=tf.ones_like(d_logits_real),
                                                          logits=d_logits_real), name='d_loss_real')
    d_loss_fake = tf.reduce_mean(
            tf.nn.sigmoid_cross_entropy_with_logits(labels=tf.zeros_like(d_logits_fake),
                                                          logits=d_logits_fake), name='d_loss_fake')
    d_loss = d_loss_real + d_loss_fake
    ae_loss = tf.reduce_mean(tf.square(X - logits))
    lambd = 1e-3
    network_loss = ae_loss + lambd*d_loss
    

with tf.name_scope('train'):
    optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
    solver = optimizer.minimize(network_loss, var_list=[enc_weights, dec_weights, disc_weights])


if is_train:
    saver = tf.train.Saver() 
    min_loss = 0
    with tf.name_scope('eval'):
        
        patience_cnt = 0
        with tf.Session() as sess:
            if is_load:
                saver.restore(sess, dir_model+'model.ckpt')
            else:
                sess.run(tf.global_variables_initializer())
                hist_d_loss = []
                hist_ae_loss = []
                hist_net_loss = []
                hist_acc = []
            for e in range(0,epoch):
                avg_ae_loss = 0
                avg_ct_loss = 0
                avg_d_loss = 0
                avg_net_loss = 0
                n_batches = len(x_batches)
                for b in range(n_batches):
                    batch_x = x_batches[b]
                    batch_x_noise = x_noise_batches[b]
                    
                    _, net_loss_val, ae_loss_val, d_loss_val = sess.run([solver, network_loss, ae_loss, d_loss], 
                                           feed_dict={X_noise: batch_x_noise, 
                                           X:batch_x})
                    avg_ae_loss = avg_ae_loss + ae_loss_val
                    avg_d_loss = avg_d_loss + d_loss_val
                    avg_net_loss = avg_net_loss + net_loss_val
                    
                avg_ae_loss = avg_ae_loss / n_batches
                avg_d_loss = avg_d_loss / n_batches
                avg_net_loss = avg_net_loss / n_batches
                hist_ae_loss.append(avg_ae_loss)
                hist_d_loss.append(avg_d_loss)
                hist_net_loss.append(avg_net_loss)
                if e % display_step == 0:
                    print('epoch:', '%04d'%(e),
                          'cost_net:', '{:.6f}'.format(avg_net_loss),
                          'cost_ae:', '{:.6f}'.format(avg_ae_loss),
                          'cost_d:', '{:.6f}'.format(avg_d_loss))
                    if min_loss == 0:
                        min_loss = avg_net_loss
                    else:
                        if avg_net_loss < min_loss:
                            min_loss = avg_net_loss
                            saver.save(sess, dir_model+'model.ckpt')
#                hist_acc.append(acc)
                if epoch > 0 and hist_net_loss[e-1] - hist_net_loss[e] > min_delta:
                    patience_cnt = 0
                else:
                    patience_cnt += 1
                if patience_cnt > patience:
                    print('epoch:', '%04d'%(e),
                          'cost_net:', '{:.6f}'.format(avg_net_loss),
                          'cost_ae:', '{:.6f}'.format(avg_ae_loss),
                          'cost_d:', '{:.6f}'.format(avg_d_loss))
                    break

