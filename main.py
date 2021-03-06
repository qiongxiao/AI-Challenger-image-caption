__author__ = 'sherlock'

import os
import time

import torch
from torch import nn, optim
from torch.autograd import Variable
from torch.nn.utils.rnn import pack_padded_sequence

from caption_model import CaptionModel
from data_utils import get_loader


def train_epoch(model, dataloader, criterion, optimizer, print_step):
    model.train()

    running_loss = 0.
    total_loss = 0.
    n_total = 0.
    for i, data in enumerate(dataloader):
        img, seq, length = data
        bs = img.size(0)
        img = Variable(img).cuda()
        seq = Variable(seq).cuda()
        # forward
        out = model(img, seq, length)
        label = pack_padded_sequence(seq.permute(1, 0), length)
        loss = criterion(out, label[0])
        # backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        running_loss += loss.data[0] / bs
        n_total += bs
        total_loss += loss.data[0]
        if (i + 1) % print_step == 0:
            print('{}/{} avg loss: {:.5f}'.format(
                i + 1, len(dataloader), running_loss / print_step))
            running_loss = 0.
    return total_loss / n_total


def train(epochs, save_point, model, dataloader, criterion, optimizer,
          print_step):
    for e in range(epochs):
        print('[ epoch {} ]'.format(e + 1))
        since = time.time()
        train_loss = train_epoch(model, dataloader, criterion, optimizer,
                                 print_step)
        print('loss: {:.5f}, time: {:.1f} s'.format(train_loss,
                                                    time.time() - since))

        if (e + 1) % save_point == 0:
            if not os.path.exists('./checkpoints'):
                os.mkdir('./checkpoints')
            torch.save(model.state_dict(),
                       './checkpoints/model_{}.pth'.format(e + 1))


def get_performance(out, label):
    crit = nn.CrossEntropyLoss(size_average=False)
    return crit(out, label)


def main():
    dataloader, vocab_size, n_class = get_loader(batch_size=2)

    cap_model = CaptionModel(
        embed_dim=512,
        model_name='resnet',
        total_vocab=vocab_size,
        n_class=n_class,
        hidden_size=512,
        num_layers=2)

    cap_model = cap_model.cuda()

    optimizer = optim.Adam(cap_model.get_train_param())

    train(
        epochs=100,
        save_point=10,
        model=cap_model,
        dataloader=dataloader,
        criterion=get_performance,
        optimizer=optimizer,
        print_step=100)


if __name__ == '__main__':
    main()