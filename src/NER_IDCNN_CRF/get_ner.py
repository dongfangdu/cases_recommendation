# encoding=utf8
import os
import pickle
import tensorflow as tf
from model import Model
from utils import get_logger
from utils import load_config
from data_utils import input_from_line
root_p = os.path.dirname(__file__)
with open("maps.pkl", "rb") as f:
    char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)


def ini_model():
    config = load_config("config_file")
    logger = get_logger("ner.log")
    path = os.path.join(root_p, "ckpt_IDCNN")
    # limit GPU memory
    # tf_config = tf.ConfigProto()
    # tf_config.gpu_options.allow_growth = True
    sess = tf.Session()
    # model = create_model(sess, Model, FLAGS.ckpt_path, load_word2vec, config, id_to_char, logger, False)
    print(2)
    model = Model(config, is_train=False)
    print(1)
    ckpt = tf.train.get_checkpoint_state(path)
    model.saver.restore(sess, ckpt.model_checkpoint_path)
    return sess, model
    # with tf.Session(config=tf_config) as sess:
    #     model = create_model(sess, Model, FLAGS.ckpt_path, load_word2vec, config, id_to_char, logger, False)
    #     for i in get_names(corpus_path):
    #         result = model.evaluate_line(sess, input_from_line(i, char_to_id), id_to_tag)
    #         print(result)


sess, model = ini_model()


def evaluate_line(st):
    return model.evaluate_line(sess, input_from_line(st, char_to_id), id_to_tag)


if __name__ == "__main__":
    print(evaluate_line("此事交给王亚东去办"))
    # tf.app.run(main)
    # txt_name = "ws01.txt"
    # corpus_path = "/store/disk2/text_correct/%s" % txt_name
    # with open("name_%s" % txt_name,"a",encoding="utf8") as f:
    #     for i in get_names(corpus_path):
    #         f.write("%s" % evaluate_line(i)+"\n")
    # sess.close()
