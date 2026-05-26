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
        Initializes the Feedback Manager. Loads existing feedback data, model, and feature columns. Sets the retrain threshold for when to trigger model retraining based on new feedback samples.
        """
        self.feedback_file = feedback_file
        self.model_path = model_path
        self.feature_cols_path = feature_cols_path
        self.retrain_threshold = retrain_threshold
        
        # Učitaj feature kolone - load the list of feature columns used for training the model
        self.feature_cols = joblib.load(feature_cols_path)
        
        # Učitaj postojeće feedback podatke - load existing feedback data from CSV
        self.feedback_data = self._load_feedback_data()
        
        # Broj novih primjera od zadnjeg treninga - count how many new samples have been added since the last training
        self.new_samples_count = self._count_new_samples()
    
    def _create_empty_feedback_df(self):
        """Kreira prazan DataFrame za feedback podatke. 
        Creates an empty DataFrame for feedback data with the appropriate columns."""
        columns = self.feature_cols + ['feedback_risk', 'original_prediction', 
                                       'user_confirmation', 'timestamp', 'trained']
        return pd.DataFrame(columns=columns)
    
    def _load_feedback_data(self):
        """Učitava feedback podatke iz CSV fajla. 
        Loads feedback data from a CSV file. If the file doesn't exist or is empty, it creates a new DataFrame with the appropriate columns."""
        if os.path.exists(self.feedback_file) and os.path.getsize(self.feedback_file) > 0:
            try:
                df = pd.read_csv(self.feedback_file)
                # Konvertuj stringove u numeričke vrijednosti
                for col in self.feature_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
            except pd.errors.EmptyDataError:
                print(f"Fajl {self.feedback_file} je prazan. Kreiram novi.")
                return self._create_empty_feedback_df()
        else:
            # Kreiraj novi fajl - create a new file if it doesn't exist
            return self._create_empty_feedback_df()
    
    def _save_feedback_data(self):
        """Čuva feedback podatke u CSV. - saves the feedback data to CSV."""
        self.feedback_data.to_csv(self.feedback_file, index=False)
    
    def _count_new_samples(self):
        """Broji koliko novih primjera ima od zadnjeg treninga. 
        Counts how many new samples have been added since the last training."""
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
        Adds user feedback to the database. 
        """
        # Kreiraj novi red - create a new row for the feedback data
        new_row = {}
        for col in self.feature_cols:
            new_row[col] = input_data.get(col, np.nan)
        
        # Feedback informacije - konvertuj u JSON serijabilne tipove
        new_row['original_prediction'] = str(original_prediction)
        new_row['user_confirmation'] = bool(user_agrees)
        new_row['timestamp'] = datetime.now().isoformat()
        new_row['trained'] = False
        
        if user_agrees:
            # Korisnik se slaže - koristi originalnu predikciju - if the user agrees, use the original prediction as feedback risk
            new_row['feedback_risk'] = 1 if original_prediction == 'High' else 0
        else:
            # Korisnik se ne slaže - treba postaviti naknadno - if the user disagrees, we will set feedback_risk to None for now and update it later when the correct risk is provided
            new_row['feedback_risk'] = None
        
        # Dodaj u DataFrame - add the new row to the feedback DataFrame
        self.feedback_data = pd.concat([self.feedback_data, pd.DataFrame([new_row])], 
                                        ignore_index=True)
        
        # Sačuvaj u CSV - save the updated feedback data to CSV
        self._save_feedback_data()
        
        # Provjeri da li treba retrain-ati model - check if we need to retrain the model based on the new samples count
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
        Updates the feedback with the correct risk (when the user disagrees).
        """
        # Pronađi zadnji unos sa istim podacima i bez feedback_risk -  find the last entry with the same input data and no feedback risk set
        mask = (self.feedback_data['user_confirmation'] == False) & \
               (self.feedback_data['feedback_risk'].isna())
        
        if mask.any():
            last_idx = self.feedback_data[mask].index[-1]
            self.feedback_data.loc[last_idx, 'feedback_risk'] = 1 if correct_risk == 'High' else 0
            self._save_feedback_data()
    
    def retrain_model(self, force=False):
        """
        Ponovo trenira model koristeći originalne podatke + feedback podatke. 
        Retrains the model using original data + feedback data. If 'force' is True, it will retrain regardless of the number of new samples.
        """
        if not force and self.new_samples_count < self.retrain_threshold:
            return {
                'success': False,
                'message': f'Nedovoljno novih primjera. Trenutno: {self.new_samples_count}/{self.retrain_threshold}'
            }
        
        # Pripremi podatke za trening - prepare the data for training
        X_list = []
        y_list = []
        
        # 1. Učitaj originalne podatke - load the original training data
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
            print(f"Učitano {len(X_original)} originalnih primjera")
        except Exception as e:
            print(f"Greška pri učitavanju originalnih podataka: {e}")
        
        # 2. Dodaj feedback primjere koji imaju validan feedback_risk - add feedback examples that have a valid feedback risk
        feedback_valid = self.feedback_data[self.feedback_data['feedback_risk'].notna()].copy()
        if len(feedback_valid) > 0:
            X_feedback = feedback_valid[self.feature_cols]
            y_feedback = feedback_valid['feedback_risk']
            
            # Očisti NaN vrijednosti - clean NaN values from the feedback data
            valid_idx = X_feedback.notna().all(axis=1)
            X_feedback = X_feedback[valid_idx]
            y_feedback = y_feedback[valid_idx]
            
            if len(X_feedback) > 0:
                X_list.append(X_feedback)
                y_list.append(y_feedback)
                print(f"✅ Učitano {len(X_feedback)} feedback primjera")
        
        # Kombinuj sve podatke - combine all the data for training
        if not X_list:
            return {'success': False, 'message': 'Nema podataka za trening'}
        
        X_combined = pd.concat(X_list, ignore_index=True)
        y_combined = pd.concat(y_list, ignore_index=True)
        
        print(f"\nUkupno podataka za trening: {len(X_combined)}")
        
        # Treniraj novi model - train a new model using the combined data
        print("Treniranje novog Random Forest modela...")
        
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
        
        # Evaluacija - evaluate the new model on the combined training data to check accuracy before saving
        from sklearn.metrics import accuracy_score
        y_pred = new_model.predict(X_combined)
        accuracy = accuracy_score(y_combined, y_pred)
        
        print(f"Accuracy na trening skupu: {accuracy:.4f}")
        
        # Sačuvaj novi model - save the new model to disk
        joblib.dump(new_model, self.model_path)
        
        # Označi sve feedback primjere kao trained - mark all feedback examples as trained
        self.feedback_data['trained'] = True
        self._save_feedback_data()
        
        # Resetuj brojač novih primjera - reset the new samples count after retraining
        self.new_samples_count = self._count_new_samples()
        
        return {
            'success': True,
            'message': f'Model uspješno retrainan! Accuracy: {accuracy:.4f}',
            'total_samples': int(len(X_combined)),
            'feedback_samples': int(len(feedback_valid)),
            'accuracy': float(accuracy)
        }
    
    def get_stats(self):
        """Vraća statistike o feedback sistemu. 
        Returns statistics about the feedback system."""
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

# Globalna instanca
_feedback_manager = None

def get_feedback_manager():
    """Dohvata ili kreira globalnu instancu FeedbackManager-a. 
    Retrieves or creates a global instance of the FeedbackManager. This ensures that we have a single instance managing the feedback data and model retraining across the application."""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackManager()
    return _feedback_manager