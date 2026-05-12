"""
feedback_manager.py
Sistem za prikupljanje feedback-a i inkrementalno učenje.
"""

import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier


class FeedbackManager:
    def __init__(self, feedback_file='models/feedback_data.csv', 
                 model_path='models/rf_model.pkl',
                 feature_cols_path='models/feature_cols_rf.pkl',
                 retrain_threshold=10):
        """
        Inicijalizacija Feedback Manager-a.
        """
        self.feedback_file = feedback_file
        self.model_path = model_path
        self.feature_cols_path = feature_cols_path
        self.retrain_threshold = retrain_threshold
        
        # Učitaj feature kolone
        self.feature_cols = joblib.load(feature_cols_path)
        
        # Učitaj postojeće feedback podatke
        self.feedback_data = self._load_feedback_data()
        
        # Broj novih primjera od zadnjeg treninga
        self.new_samples_count = self._count_new_samples()
    
    def _create_empty_feedback_df(self):
        """Kreira prazan DataFrame za feedback podatke."""
        columns = self.feature_cols + ['feedback_risk', 'original_prediction', 
                                       'user_confirmation', 'timestamp', 'trained']
        return pd.DataFrame(columns=columns)
    
    def _load_feedback_data(self):
        """Učitava feedback podatke iz CSV fajla."""
        if os.path.exists(self.feedback_file) and os.path.getsize(self.feedback_file) > 0:
            try:
                df = pd.read_csv(self.feedback_file)
                # Konvertuj stringove u numeričke vrijednosti
                for col in self.feature_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except pd.errors.EmptyDataError:
                print(f"⚠️ Fajl {self.feedback_file} je prazan. Kreiram novi.")
                return self._create_empty_feedback_df()
        else:
            # Kreiraj novi fajl
            return self._create_empty_feedback_df()
    
    def _save_feedback_data(self):
        """Čuva feedback podatke u CSV."""
        self.feedback_data.to_csv(self.feedback_file, index=False)
    
    def _count_new_samples(self):
        """Broji koliko novih primjera ima od zadnjeg treninga."""
        if len(self.feedback_data) == 0:
            return 0
        
        if 'trained' in self.feedback_data.columns:
            not_trained = self.feedback_data['trained'] != True
            return int(not_trained.sum())
        else:
            return int(len(self.feedback_data))
    
    def add_feedback(self, input_data, original_prediction, user_agrees):
        """
        Dodaje feedback korisnika u bazu.
        """
        # Kreiraj novi red
        new_row = {}
        for col in self.feature_cols:
            new_row[col] = input_data.get(col, np.nan)
        
        # Feedback informacije - konvertuj u JSON serijabilne tipove
        new_row['original_prediction'] = str(original_prediction)
        new_row['user_confirmation'] = bool(user_agrees)
        new_row['timestamp'] = datetime.now().isoformat()
        new_row['trained'] = False
        
        if user_agrees:
            # Korisnik se slaže - koristi originalnu predikciju
            new_row['feedback_risk'] = 1 if original_prediction == 'High' else 0
        else:
            # Korisnik se ne slaže - treba postaviti naknadno
            new_row['feedback_risk'] = None
        
        # Dodaj u DataFrame
        self.feedback_data = pd.concat([self.feedback_data, pd.DataFrame([new_row])], 
                                        ignore_index=True)
        
        # Sačuvaj u CSV
        self._save_feedback_data()
        
        # Provjeri da li treba retrain-ati model
        self.new_samples_count = self._count_new_samples()
        
        result = {
            'success': True,
            'feedback_saved': True,
            'new_samples_count': int(self.new_samples_count),
            'retrain_threshold': int(self.retrain_threshold),
            'needs_retraining': bool(self.new_samples_count >= self.retrain_threshold)
        }
        
        return result
    
    def update_feedback_risk(self, input_data, correct_risk):
        """
        Ažurira feedback sa tačnim rizikom (kada se korisnik ne slaže).
        """
        # Pronađi zadnji unos sa istim podacima i bez feedback_risk
        mask = (self.feedback_data['user_confirmation'] == False) & \
               (self.feedback_data['feedback_risk'].isna())
        
        if mask.any():
            last_idx = self.feedback_data[mask].index[-1]
            self.feedback_data.loc[last_idx, 'feedback_risk'] = 1 if correct_risk == 'High' else 0
            self._save_feedback_data()
    
    def retrain_model(self, force=False):
        """
        Ponovo trenira model koristeći originalne podatke + feedback podatke.
        """
        if not force and self.new_samples_count < self.retrain_threshold:
            return {
                'success': False,
                'message': f'Nedovoljno novih primjera. Trenutno: {self.new_samples_count}/{self.retrain_threshold}'
            }
        
        # Pripremi podatke za trening
        X_list = []
        y_list = []
        
        # 1. Učitaj originalne podatke
        try:
            from model_train_rf import load_and_prepare_data
            df_original = load_and_prepare_data('data/dataset.csv')
            
            for col in self.feature_cols:
                if col in df_original.columns:
                    df_original[col] = pd.to_numeric(df_original[col], errors='coerce')
            
            X_original = df_original[self.feature_cols].dropna()
            y_original = df_original.loc[X_original.index, 'nivo_rizika']
            y_original = y_original.map({'Low': 0, 'High': 1})
            
            X_list.append(X_original)
            y_list.append(y_original)
            print(f"✅ Učitano {len(X_original)} originalnih primjera")
        except Exception as e:
            print(f"⚠️ Greška pri učitavanju originalnih podataka: {e}")
        
        # 2. Dodaj feedback primjere koji imaju validan feedback_risk
        feedback_valid = self.feedback_data[self.feedback_data['feedback_risk'].notna()].copy()
        if len(feedback_valid) > 0:
            X_feedback = feedback_valid[self.feature_cols]
            y_feedback = feedback_valid['feedback_risk']
            
            # Očisti NaN vrijednosti
            valid_idx = X_feedback.notna().all(axis=1)
            X_feedback = X_feedback[valid_idx]
            y_feedback = y_feedback[valid_idx]
            
            if len(X_feedback) > 0:
                X_list.append(X_feedback)
                y_list.append(y_feedback)
                print(f"✅ Učitano {len(X_feedback)} feedback primjera")
        
        # Kombinuj sve podatke
        if not X_list:
            return {'success': False, 'message': 'Nema podataka za trening'}
        
        X_combined = pd.concat(X_list, ignore_index=True)
        y_combined = pd.concat(y_list, ignore_index=True)
        
        print(f"\n📊 Ukupno podataka za trening: {len(X_combined)}")
        
        # Treniraj novi model
        print("🧠 Treniranje novog Random Forest modela...")
        
        new_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            verbose=1
        )
        
        new_model.fit(X_combined, y_combined)
        
        # Evaluacija
        from sklearn.metrics import accuracy_score
        y_pred = new_model.predict(X_combined)
        accuracy = accuracy_score(y_combined, y_pred)
        
        print(f"📈 Accuracy na trening skupu: {accuracy:.4f}")
        
        # Sačuvaj novi model
        joblib.dump(new_model, self.model_path)
        
        # Označi sve feedback primjere kao trained
        self.feedback_data['trained'] = True
        self._save_feedback_data()
        
        # Resetuj brojač novih primjera
        self.new_samples_count = self._count_new_samples()
        
        return {
            'success': True,
            'message': f'Model uspješno retrainan! Accuracy: {accuracy:.4f}',
            'total_samples': int(len(X_combined)),
            'feedback_samples': int(len(feedback_valid)),
            'accuracy': float(accuracy)
        }
    
    def get_stats(self):
        """Vraća statistike o feedback sistemu."""
        total_feedback = len(self.feedback_data)
        
        if total_feedback == 0:
            return {
                'total_feedback': 0,
                'agreed_with_model': 0,
                'disagreed_with_model': 0,
                'pending_correction': 0,
                'trained_samples': 0,
                'new_samples_pending': 0,
                'retrain_threshold': int(self.retrain_threshold),
                'needs_retraining': False
            }
        
        agreed = int(len(self.feedback_data[self.feedback_data['user_confirmation'] == True]))
        disagreed = int(len(self.feedback_data[self.feedback_data['user_confirmation'] == False]))
        pending = int(len(self.feedback_data[self.feedback_data['feedback_risk'].isna()]))
        trained = int(len(self.feedback_data[self.feedback_data['trained'] == True])) if 'trained' in self.feedback_data.columns else 0
        
        return {
            'total_feedback': int(total_feedback),
            'agreed_with_model': agreed,
            'disagreed_with_model': disagreed,
            'pending_correction': pending,
            'trained_samples': trained,
            'new_samples_pending': int(self.new_samples_count),
            'retrain_threshold': int(self.retrain_threshold),
            'needs_retraining': bool(self.new_samples_count >= self.retrain_threshold)
        }

def _save_model_version(self, version_info=None):
    """Čuva informacije o verziji modela."""
    version_file = os.path.join(os.path.dirname(self.model_path), 'model_version.txt')
    
    if version_info is None:
        version_info = {
            'version': self._get_next_version(),
            'timestamp': datetime.now().isoformat(),
            'total_samples': len(self.feedback_data),
            'feedback_samples': len(self.feedback_data[self.feedback_data['feedback_risk'].notna()]) if len(self.feedback_data) > 0 else 0
        }
    
    with open(version_file, 'w') as f:
        f.write(f"Model Version: {version_info['version']}\n")
        f.write(f"Trained: {version_info['timestamp']}\n")
        f.write(f"Total Samples: {version_info['total_samples']}\n")
        f.write(f"Feedback Samples: {version_info['feedback_samples']}\n")
    
    print(f"✅ Verzija modela sačuvana: {version_info['version']}")

def _get_next_version(self):
    """Dohvata sljedeći broj verzije."""
    version_file = os.path.join(os.path.dirname(self.model_path), 'model_version.txt')
    
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('Model Version:'):
                    current = line.split(':')[1].strip()
                    try:
                        # Ako je verzija broj (npr. 1, 2, 3...)
                        next_version = int(current) + 1
                        return str(next_version)
                    except ValueError:
                        # Ako je verzija u formatu v1.0, v2.0...
                        import re
                        match = re.search(r'(\d+)', current)
                        if match:
                            next_version = int(match.group(1)) + 1
                            return f"v{next_version}.0"
        return "2.0"
    else:
        return "1.0"

def _load_model_version(self):
    """Učitava informacije o verziji modela."""
    version_file = os.path.join(os.path.dirname(self.model_path), 'model_version.txt')
    
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            content = f.read()
        return content
    return "No version info available"

# Globalna instanca
_feedback_manager = None

def get_feedback_manager():
    """Dohvata ili kreira globalnu instancu FeedbackManager-a."""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackManager()
    return _feedback_manager