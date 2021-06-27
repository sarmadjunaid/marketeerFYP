import random
import re
import csv
import random
import os
import speech_recognition as sr
import torch
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from googletrans import Translator
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from aitextgen import aitextgen

from .forms import SignUpForm
from .models import Product, Description

key = []
des = []
array = []
array2 = []
x = 0


def multi_sub(pairs, s):
    def repl_func(m):
        # only one group will be present, use the corresponding match
        return next(
            repl
            for (patt, repl), group in zip(pairs, m.groups())
            if group is not None
        )

    pattern = '|'.join("({})".format(patt) for patt, _ in pairs)
    return re.sub(pattern, repl_func, s)


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def home(request):
    count = User.objects.count()
    return render(request, 'home.html', {
        'count': count,
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {
        'form': form,
    })


def suggestion():
    lines = []
    a = random.randint(0, 458)
    b = a + 4
    print(a)
    print(b)

    with open('list_attr_cloth.txt', 'r') as f:
        for index, text in enumerate(f):
            if a <= index <= b:
                lines.append(text)
    return lines


@login_required
def dashboard(request):
    lines = suggestion()
    return render(request, 'dashboard.html', {
        'lines': lines
    })


def generate_description(request):
    # function to generate description
    global keywords
    global adj
    global desc
    global text
    global brnd
    global category
    global male, female

    lines = suggestion()

    if request.method == "POST":
        keywords = request.POST.get("keywords")
        brnd = request.POST.get("name")
        category = request.POST.get("male")
        adj = request.POST.get("adj")

        output_dir = 'accounts/MenModel/'
        # output_dir = os.path.join(settings.FILES_DIR, 'MenModel')
        print(category)
        if category == 'dress':
            output_dir = 'accounts/WomenModel/'

        ai = aitextgen(model_folder=output_dir, to_gpu=False)
        status = True
        array2 = descriptions()
        while status == True:
            desc = ai.generate_one(
                batch_size=5,
                prompt=keywords,
                max_length=256,
                temperature=1.0,
                top_p=0.9)

            status = plagcheck(array2, desc)
            print(status)

        if brnd is not None:
            brands = []
            with open('accounts/brands.csv', encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    brands.append(row[0])

            for brand in brands:
                desc = re.sub(' ' + brand + ' ', ' ' + brnd + ' ', desc)

    key.append(keywords)
    des.append(desc)

    translator = Translator()
    result = translator.translate(desc, src='en', dest='ur')
    translated = result.text

    context = {'desc': desc, "keywords": keywords, "name": brnd, "key": key, "des": des, 'lines': lines, 'translated': translated}

    return render(request, 'dashboard.html', context)


def descriptions():
    descriptions = Description.objects.all()
    print(descriptions)
    for description in descriptions:
        array.append(str(description))

    return array


def plagcheck(descriptionray, text):
    import re
    import string
    import contractions
    import spacy

    def chunkify(text):
        en = spacy.load('en_core_web_sm')

        doc = en(text)
        # deplacy.render(doc)
        # Lets see how this goes.This should result in 100% similarity. This is a dummy text to

        seen = set()  # keep track of covered words

        chunks = []
        for sent in doc.sents:
            heads = [cc for cc in sent.root.children if cc.dep_ == 'conj']

            for head in heads:
                words = [ww for ww in head.subtree]
                for word in words:
                    seen.add(word)
                chunk = (' '.join([ww.text for ww in words]))
                chunks.append((head.i, chunk))

            unseen = [ww for ww in sent if ww not in seen]
            chunk = ' '.join([ww.text for ww in unseen])
            chunks.append((sent.root.i, chunk))

        chunks = sorted(chunks, key=lambda x: x[0])

        return (chunks)

    counter1 = 0
    counter2 = 0
    counter = 0
    counter3 = 0
    chunk2array = []
    chunk1array = []
    chunkSplit = []
    chunk2Split = []
    mainsamearray = []
    similardesc = []
    RejectDesc = False
    word = ' '
    word2 = ' '
    same = 0
    total = 0
    totalpvalue = 0
    desCount = 0
    tcp = 0
    f = []
    c2 = 0
    c3 = 0
    # This is a dummy text to see if this works. This should result in 100% similarity. Lets see how this goes
    # text="67: This pink dress from BRANDNAME makes a wonderful option to add to your formalwear wardrobe. Made with fluted sleeves and a flowing hem for a fluid silhouette, it's styled with a ruched v-neckline and long sleeves with button detailing. Finished with a sweetheart neckline and two concealed pockets, this dress pairs perfectly with strappy heels to party-proof your look. "
    text = contractions.fix(text)

    chunks = chunkify(text)

    # f = open("sampleset.txt", "r")
    f = descriptionray
    for descr2 in f:
        if str(descr2).isspace() is False and RejectDesc is False:

            descr2 = contractions.fix(descr2)
            chunks2 = chunkify(descr2)
            counter = 0

            for ii, chunk in chunks:

                chunkSplit = chunk.split()

                if len(chunkSplit) == 2:
                    continue

                counter = 0
                highest = 0
                for zz, line in chunks2:
                    chunk2Split = line.split()
                    comparestatus = 0
                    if len(chunk2Split) == 2:
                        continue

                    notok = 0

                    if line.isspace() == False:

                        while comparestatus == 0:
                            if chunkSplit[counter1].isdigit():
                                if counter1 + 1 < len(chunkSplit):
                                    counter1 = counter1 + 1

                            if chunk2Split[counter2].isdigit():
                                if counter2 + 1 < len(chunk2Split):
                                    counter2 = counter2 + 1

                            if counter1 + 1 < len(chunkSplit):
                                if chunkSplit[counter1 + 1] == "'s":
                                    chunkSplit[counter1 + 1] = chunkSplit[counter1] + chunkSplit[counter1 + 1]

                                    counter1 = counter1 + 1

                            if counter2 + 1 < len(chunk2Split):
                                if chunk2Split[counter2 + 1] == "'s":
                                    chunk2Split[counter2 + 1] = chunk2Split[counter2] + chunk2Split[counter2 + 1]

                                    counter2 = counter2 + 1

                            if counter1 + 2 < len(chunkSplit):
                                if chunkSplit[counter1 + 1] == '-':
                                    chunkSplit[counter1 + 2] = chunkSplit[counter1] + chunkSplit[counter1 + 1] + \
                                                               chunkSplit[counter1 + 2]

                                    counter1 = counter1 + 2
                                    if chunkSplit[counter1 + 1] == '-':
                                        chunkSplit[counter1 + 2] = chunkSplit[counter1 + 1] + chunkSplit[counter1 + 2]
                                        counter1 = counter1 + 2

                            if counter2 + 2 < len(chunk2Split):
                                if chunk2Split[counter2 + 1] == '-':
                                    chunk2Split[counter2 + 2] = chunk2Split[counter2] + chunk2Split[counter2 + 1] + \
                                                                chunk2Split[counter2 + 2]

                                    counter2 = counter2 + 2
                                    if chunk2Split[counter2 + 1] == '-':
                                        chunk2Split[counter2 + 1] = chunk2Split[counter2] + chunk2Split[counter2 + 1]
                                        counter2 = counter2 + 2

                            if chunkSplit[counter1] in string.punctuation:

                                if counter1 + 1 < len(chunkSplit):
                                    counter1 = counter1 + 1
                            if chunk2Split[counter2] in string.punctuation:

                                if counter2 + 1 < len(chunk2Split):
                                    counter2 = counter2 + 1

                            if chunkSplit[counter1].lower() == chunk2Split[counter2].lower():

                                same = same + 1
                                counter1 = counter1 + 1
                                counter2 = counter2 + 1
                                total = total + 1
                                notok = 0


                            else:

                                counter2 = counter2 + 1
                                total = total + 1
                                notok = notok + 1

                            if counter1 == len(chunkSplit) or counter2 >= len(chunk2Split) or notok >= 4:
                                comparestatus = 1

                            response = True
                            response2 = True

                        similarity = (same / total * 100)
                        if similarity > highest:
                            highest = similarity

                        total = 0
                        same = 0
                        counter1 = 0
                        counter2 = 0
                        similarity = 0
                        counter = counter + 1

                    c2 = c2 + 1

                c2 = 0
                mainsamearray.append(highest)
                totalpvalue = totalpvalue + highest
                cp = totalpvalue / (counter * 100) * 100

                counter3 = counter3 + 1
                totalpvalue = 0
                tcp = cp + tcp
                c3 = c3 + 1
                # print("NEW TCP VALUE IS ", tcp)

            print("\n")
            summ = 0
            for i in mainsamearray:
                summ = summ + i

            if summ / (c3 * 100) * 100 >= 30:
                print("************************************")
                print("\n")
                print("THE DESCRIPTION IS SIMILAR TO THE ONE BEING COMPARED")
                similardesc.append(desCount)
                print("Therefore the core description is now rejected")
                RejectDesc = True
                print("************************************")
                print("\n\n")

            tcp = 0
            c3 = 0
            mainsamearray = []
            desCount = desCount + 1

    for i in similardesc:
        print(i)
    return RejectDesc


def save_description(request):
    if request.method == 'POST':
        product, created = Product.objects.get_or_create(
            name=brnd,
            user=request.user
        )

        description = Description(
            keywords=keywords,
            text=desc,
            product=product
        )
        description.save()
        lines = suggestion()
    return render(request, 'dashboard.html', lines)



def translate(request):
    translator = Translator()
    result = translator.translate(desc, src='en', dest='ur')
    translated = result.text
    print(translated)
    lines = suggestion()
    context = {'translated_text': translated, 'lines': lines}

    return render(request, 'dashboard.html', context)


@login_required
def product_list(request):
    print(request.user.id)
    cursor = connection.cursor()
    query = '''SELECT *
                FROM (SELECT id, username FROM auth_user) auth_user
                LEFT OUTER JOIN (SELECT * FROM accounts_product) accounts_product ON auth_user.id = accounts_product.user_id
                LEFT OUTER JOIN (SELECT * FROM accounts_description) accounts_description ON accounts_product.id = accounts_description.product_id
                WHERE user_id = 1'''
    cursor.execute(query)
    products = dictfetchall(cursor)
    print(products)
    print(type(products))
    print(products[1]['name'])
    return render(request, 'pro_list.html', {
        'products': products,
    })


def deleteDescription(request, pk):
    print(pk)
    item = get_object_or_404(Description, id=pk)
    product = item.product
    if request.method == 'POST':
        item.delete()
        product.delete()
        return redirect('/prod_list')

    context = {'item': item}
    return render(request, "delete.html", context)
