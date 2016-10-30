# TODO sanity check pred, 
# generate and plot,
# upscale-downscale-q_level
# validation

import tensorflow as tf
import numpy as np
from models import PixelCNN
from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("data/")
epochs = 10
batch_size = 50
grad_clip = 1

LAYERS = 3
F_MAP = 32
FILTER_SIZE = 7
CHANNEL = 1

X = tf.placeholder(tf.float32, shape=[None, 784])
X_image = tf.reshape(X, [-1, 28, 28, CHANNEL])
# TODO mean pixel value if not mnist
v_stack_in, h_stack_in = X_image, X_image

for i in range(LAYERS):
    FILTER_SIZE = 3 if i > 0 else FILTER_SIZE
    CHANNEL = F_MAP if i > 0 else CHANNEL
    mask = 'b' if i > 0 else 'a'
    i = str(i)

    with tf.name_scope("v_stack"+i):
        v_stack = PixelCNN([FILTER_SIZE, FILTER_SIZE, CHANNEL, F_MAP], [F_MAP], v_stack_in, mask=mask).output()
        v_stack_in = v_stack

    with tf.name_scope("v_stack_1"+i):
        v_stack_1 = PixelCNN([1, 1, F_MAP, F_MAP], [F_MAP], v_stack_in, gated=False, mask=mask).output()
        
    with tf.name_scope("h_stack"+i):
        h_stack = PixelCNN([1, FILTER_SIZE, CHANNEL, F_MAP], [F_MAP], h_stack_in, gated=True, payload=v_stack_1, mask=mask).output()

    with tf.name_scope("h_stack_1"+i):
        h_stack_1 = PixelCNN([1, 1, F_MAP, F_MAP], [F_MAP], h_stack, gated=False, mask=mask).output()
        h_stack_1 += h_stack_in
        h_stack_in = h_stack_1

with tf.name_scope("fc_1"):
    fc1 = PixelCNN([1, 1, F_MAP, F_MAP],[F_MAP], h_stack_in, gated=False, mask='b').output()
# handle Imagenet differently
with tf.name_scope("fc_2"):
    fc2 = PixelCNN([1, 1, F_MAP, 1],[1], fc1, gated=False, mask='b', activation=False).output()
pred = tf.nn.sigmoid(fc2)

loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(fc2, X_image))

trainer = tf.train.RMSPropOptimizer(1e-3)
gradients = trainer.compute_gradients(loss)

clipped_gradients = [(tf.clip_by_value(_[0], -grad_clip, grad_clip), _[1]) for _ in gradients]
optimizer = trainer.apply_gradients(clipped_gradients)

#correct_preds = tf.equal(tf.argmax(X,1), tf.argmax(pred, 1))
#accuracy = tf.reduce_mean(tf.cast(correct_preds, tf.float32))

#summary = tf.train.SummaryWriter('logs', sess.graph)

with tf.Session() as sess: 
    sess.run(tf.initialize_all_variables())
    for i in range(epochs):
        batch_X = mnist.train.next_batch(batch_size)[0]
        _, cost = sess.run([optimizer, loss], feed_dict={X:batch_X})
        print cost
        
        #if i%1 == 0:
            #print accuracy.eval(feed_dict={X:batch_X})
    #print accuracy.eval(feed_dict={X:mnist.test.images})
