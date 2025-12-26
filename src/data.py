import torch
import numpy as np
from torch.utils.data import DataLoader, Dataset 
import os 
from PIL import Image 
import albumentations as A
import numpy as np
from colorama import Fore 
from matplotlib import pyplot as plt 
from utils.boxes import rescale_bboxes, stacker
from utils.setup import get_classes
from utils.logger import get_logger
from utils.rich_handlers import DataLoaderHandler
import sys 


class DETRData(Dataset): 
    def __init__(self, path, train=True):
        super().__init__()
        self.path = path
        self.labels_path = os.path.join(self.path, 'labels')
        self.images_path = os.path.join(self.path, 'images')
        self.label_files = os.listdir(self.labels_path) 
        self.labels = list(filter(lambda x: x.endswith('.txt'), self.label_files))
        self.train = train
        
        # Initialize logger
        self.logger = get_logger("data_loader")
        self.data_handler = DataLoaderHandler()
        
        # Log dataset initialization
        dataset_info = {
            "Dataset Path": self.path,
            "Mode": "Training" if train else "Testing",
            "Total Samples": len(self.labels),
            "Images Path": self.images_path,
            "Labels Path": self.labels_path
        }
        self.data_handler.log_dataset_stats(dataset_info)
        
        # Log transforms information
        transform_list = [
            "Resize to 500x500",
            "Random Crop 224x224 (training only)",
            "Final Resize to 224x224",
            "Horizontal Flip p=0.5 (training only)",
            "Color Jitter (training only)",
            "Normalize (ImageNet stats)",
            "Convert to Tensor"
        ]
        self.data_handler.log_transform_info(transform_list)             

    def safe_transform(self, image, bboxes, labels, max_attempts=50):
        self.transform = A.Compose(
            [   
                A.Resize(500,500),
                *([A.RandomCrop(width=224, height=224, p=0.33)] if self.train else []), # Example random crop
                A.Resize(224,224),
                *([A.HorizontalFlip(p=0.5)] if self.train else []),
                *([A.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5, hue=0.5, p=0.5)] if self.train else []),
                A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                A.ToTensorV2()
            ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'])
        )
        
        for attempt in range(max_attempts):
            try:
                transformed = self.transform(image=image, bboxes=bboxes, class_labels=labels)
                # Check if we still have bboxes after transformation
                if len(transformed['bboxes']) > 0:
                    return transformed
            except:
                continue
        
        return {'image': image, 'bboxes': bboxes, 'class_labels': labels}

    def __len__(self): 
        return len(self.labels) 

    def __getitem__(self, idx): 
        self.label_path = os.path.join(self.labels_path, self.labels[idx]) 
        self.image_name = self.labels[idx].split('.')[0]
        self.image_path = os.path.join(self.images_path, f'{self.image_name}.jpg') 
        
        img = Image.open(self.image_path)
        with open(self.label_path, 'r') as f: 
            annotations = f.readlines()
        class_labels = []
        bounding_boxes = []
        for annotation in annotations: 
            annotation = annotation.split('\n')[:-1][0].split(' ')
            class_labels.append(annotation[0]) 
            bounding_boxes.append(annotation[1:])
        class_labels = np.array(class_labels).astype(int) 
        bounding_boxes = np.array(bounding_boxes).astype(float) 

        augmented = self.safe_transform(image=np.array(img), bboxes=bounding_boxes, labels=class_labels)
        augmented_img_tensor = augmented['image']  # Already tensor from ToTensorV2()
        augmented_bounding_boxes = np.array(augmented['bboxes'])
        augmented_classes = augmented['class_labels']

        labels = torch.tensor(augmented_classes, dtype=torch.long)  
        boxes = torch.tensor(augmented_bounding_boxes, dtype=torch.float32)
        return augmented_img_tensor, {'labels': labels, 'boxes': boxes}

if __name__ == '__main__':
    dataset = DETRData('data/train', train=True) 
    
    # Get one sample from each class for better visualization
    CLASSES = get_classes()
    NUM_CLASSES = len(CLASSES)
    
    print(f"{Fore.LIGHTCYAN_EX}📊 Toplam {NUM_CLASSES} sınıf var{Fore.RESET}")
    print(f"{Fore.LIGHTGREEN_EX}Her sınıftan birer örnek toplanıyor...{Fore.RESET}\n")
    
    class_samples = {i: None for i in range(NUM_CLASSES)}
    
    # Collect one sample per class
    for idx in range(len(dataset)):
        img, annotation = dataset[idx]
        for class_id in annotation['labels']:
            class_id = class_id.item()
            if class_samples[class_id] is None:
                class_samples[class_id] = idx
                print(f"  ✅ {CLASSES[class_id]} (ID: {class_id}) - Örnek bulundu")
        
        # Check if we have samples for all classes
        if all(v is not None for v in class_samples.values()):
            print(f"\n{Fore.LIGHTGREEN_EX}🎉 Tüm sınıflar için örnek bulundu!{Fore.RESET}\n")
            break
    
    # Check which classes are missing
    missing_classes = [CLASSES[i] for i, v in class_samples.items() if v is None]
    if missing_classes:
        print(f"{Fore.LIGHTRED_EX}⚠️  Eksik sınıflar: {missing_classes}{Fore.RESET}")
    
    # Get the selected samples
    X, y, class_ids = [], [], []
    for class_id in range(NUM_CLASSES):
        if class_samples[class_id] is not None:
            idx = class_samples[class_id]
            img, annotation = dataset[idx]
            X.append(img)
            y.append(annotation)
            class_ids.append(class_id)
    
    X = torch.stack(X)
    
    print(f"\n{Fore.LIGHTGREEN_EX}📋 Seçilen örnekler:{Fore.RESET}")
    for i, (ann, cls_id) in enumerate(zip(y, class_ids)):
        class_names = [CLASSES[label.item()] for label in ann['labels']]
        print(f"  Görsel {i+1}: {class_names} (ID: {cls_id})")
    
    # Calculate grid size (make it square-ish)
    num_samples = len(X)
    cols = int(np.ceil(np.sqrt(num_samples)))
    rows = int(np.ceil(num_samples / cols))
    
    print(f"\n{Fore.LIGHTCYAN_EX}📊 Görselleştirme: {rows}x{cols} grid ({num_samples} görsel){Fore.RESET}\n")
    
    fig, ax = plt.subplots(rows, cols, figsize=(cols*4, rows*4))
    axs = ax.flatten() if num_samples > 1 else [ax]
    
    for idx, (img, annotations, ax, cls_id) in enumerate(zip(X, y, axs, class_ids)): 
        # Convert tensor to numpy for matplotlib
        img_np = img.permute(1,2,0).detach().cpu().numpy()
        ax.imshow(img_np)
        ax.set_title(f'{CLASSES[cls_id]} (ID: {cls_id})', fontsize=12, fontweight='bold')
        ax.axis('off')
        
        box_classes = annotations['labels'] 
        boxes = rescale_bboxes(annotations['boxes'], (224,224))
        for box_class, bbox in zip(box_classes, boxes): 
            xmin, ymin, xmax, ymax = bbox.detach().numpy()
            ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, color=(0.000, 0.447, 0.741), linewidth=3))
            text = f'{CLASSES[box_class]}'
            ax.text(xmin, ymin, text, fontsize=10, bbox=dict(facecolor='yellow', alpha=0.5))
    
    # Hide extra subplots if any
    for idx in range(num_samples, len(axs)):
        axs[idx].axis('off')

    plt.suptitle(f'Tüm Sınıflar - {NUM_CLASSES} Farklı İşaret', fontsize=16, fontweight='bold')
    fig.tight_layout() 
    plt.show()     